use anyhow::{Context, Result};
use clap::Parser;
use crossterm::event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode};
use crossterm::terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph, Wrap};
use ratatui::Terminal;
use std::process::Stdio;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;
use tokio::sync::mpsc;
use tokio::time::{sleep, Duration};

#[derive(Parser, Debug, Clone)]
#[command(name = "ocean-tui")]
struct Args {
    /// Start in read-only mode (no commands executed)
    #[arg(long)]
    read_only: bool,
}

#[derive(Default, Clone)]
struct AppState {
    chat: Vec<String>,
    chat_scroll: usize,
    backlog: Vec<String>,
    queues: Vec<String>,
    approvals: Vec<String>,
    logs: Vec<String>,
    status: String,
    input: String,
    input_mode: bool,
    show_sidebar: bool,
    show_backlog: bool,
    show_logs: bool,
    spinner: usize,
}

enum AppEvent {
    AppendChat(String),
    SetStatus(String),
    ReplaceBacklog(Vec<String>),
    ReplaceLogs(Vec<String>),
    ReplaceApprovals(Vec<String>),
    Tick,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // TUI setup
    enable_raw_mode()?;
    let mut stdout = std::io::stdout();
    crossterm::execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Channels
    let (tx, mut rx) = mpsc::unbounded_channel::<AppEvent>();

    let mut app = AppState::default();
    app.queues = vec![
        "Codex Queue: idle".to_string(),
        "Ocean Queue: idle".to_string(),
        "Approvals: none".to_string(),
    ];
    app.backlog = vec!["(empty)".to_string()];
    app.logs = Vec::new();
    app.approvals = Vec::new();
    app.status = "Ready".to_string();
    app.chat.push("🌊 Ocean TUI — type : to enter command mode, q to quit".into());
    app.show_sidebar = true;
    app.show_backlog = true;
    app.show_logs = true;

    // initial backlog load (best-effort)
    let tx_init = tx.clone();
    tokio::spawn(async move {
        if let Ok(text) = tokio::fs::read_to_string("docs/backlog.json").await {
            let mut lines = Vec::new();
            lines.push(format!("{} bytes loaded", text.len()));
            let _ = tx_init.send(AppEvent::ReplaceBacklog(lines));
        }
    });

    // Tail latest session log (best-effort)
    let tx_logs = tx.clone();
    tokio::spawn(async move {
        loop {
            let mut latest: Option<std::path::PathBuf> = None;
            if let Ok(mut rd) = tokio::fs::read_dir("logs").await {
                while let Ok(Some(entry)) = rd.next_entry().await {
                    if let Ok(name) = entry.file_name().into_string() {
                        if name.starts_with("session-") && name.ends_with(".log") {
                            latest = Some(entry.path());
                        }
                    }
                }
            }
            if let Some(p) = latest {
                if let Ok(s) = tokio::fs::read_to_string(p).await {
                    let mut last: Vec<String> = s.lines().rev().take(200).rev().map(|x| x.to_string()).collect();
                    let _ = tx_logs.send(AppEvent::ReplaceLogs(last.clone()));
                    // naive approvals extraction
                    let approvals: Vec<String> = last.iter().filter(|l| l.contains("[ASK]") || l.contains("[APPROVAL]")).cloned().collect();
                    if !approvals.is_empty() {
                        let _ = tx_logs.send(AppEvent::ReplaceApprovals(approvals));
                    }
                }
            }
            sleep(Duration::from_millis(1500)).await;
        }
    });

    // Tick for spinner/animation
    let tx_tick = tx.clone();
    tokio::spawn(async move {
        loop {
            sleep(Duration::from_millis(250)).await;
            let _ = tx_tick.send(AppEvent::Tick);
        }
    });

    // Main loop
    loop {
        terminal.draw(|f| ui(f, &app))?;
        // handle async events
        while let Ok(ev) = rx.try_recv() {
            match ev {
                AppEvent::AppendChat(s) => app.chat.push(s),
                AppEvent::SetStatus(s) => app.status = s,
                AppEvent::ReplaceBacklog(v) => app.backlog = v,
                AppEvent::ReplaceLogs(v) => app.logs = v,
                AppEvent::ReplaceApprovals(v) => app.approvals = v,
                AppEvent::Tick => app.spinner = (app.spinner + 1) % 4,
            }
        }
        // handle input events
        if event::poll(Duration::from_millis(100))? {
            match event::read()? {
                Event::Key(k) => match k.code {
                    KeyCode::Char('q') if !app.input_mode => break,
                    KeyCode::Char('s') if !app.input_mode => { app.show_sidebar = !app.show_sidebar; }
                    KeyCode::Char('b') if !app.input_mode => { app.show_backlog = !app.show_backlog; }
                    KeyCode::Char('l') if !app.input_mode => { app.show_logs = !app.show_logs; }
                    KeyCode::Char('?') if !app.input_mode => {
                        app.chat.push("Keys: q quit • : command • s sidebar • b backlog • l logs • PgUp/PgDn scroll".into());
                    }
                    KeyCode::PageUp if !app.input_mode => { app.chat_scroll = app.chat_scroll.saturating_add(3); }
                    KeyCode::PageDown if !app.input_mode => { app.chat_scroll = app.chat_scroll.saturating_sub(3); }
                    KeyCode::Char(':') if !app.input_mode => {
                        app.input_mode = true;
                        app.input.clear();
                    }
                    KeyCode::Esc => {
                        app.input_mode = false;
                        app.status = "Ready".into();
                    }
                    KeyCode::Enter if app.input_mode => {
                        let cmdline = app.input.clone();
                        app.input_mode = false;
                        app.status = format!("Running: {}", cmdline);
                        let _ = tx.send(AppEvent::AppendChat(format!("→ {}", cmdline)));
                        if !args.read_only {
                            spawn_cmd(cmdline, tx.clone()).await?;
                        } else {
                            let _ = tx.send(AppEvent::AppendChat("(read-only)".into()));
                        }
                    }
                    KeyCode::Char(c) if app.input_mode => app.input.push(c),
                    KeyCode::Backspace if app.input_mode => {
                        app.input.pop();
                    }
                    _ => {}
                },
                _ => {}
            }
        }
    }

    // teardown
    disable_raw_mode()?;
    crossterm::execute!(terminal.backend_mut(), LeaveAlternateScreen, DisableMouseCapture)?;
    terminal.show_cursor()?;
    Ok(())
}

fn ui<'a>(f: &mut Terminal<CrosstermBackend<std::io::Stdout>>::Frame, app: &AppState) {
    let size = f.size();
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(5),  // main
            Constraint::Length(3), // input
            Constraint::Length(if app.show_logs { 5 } else { 1 }), // logs/status
        ])
        .split(size);

    // Determine sidebar/backlog widths
    let mut h_constraints: Vec<Constraint> = Vec::new();
    if app.show_sidebar { h_constraints.push(Constraint::Length(30)); }
    h_constraints.push(Constraint::Min(20));
    if app.show_backlog { h_constraints.push(Constraint::Length(30)); }

    let main_layout = Layout::default()
        .direction(Direction::Horizontal)
        .constraints(h_constraints)
        .split(chunks[0]);

    let mut idx = 0;
    if app.show_sidebar {
        // Sidebar (Queues/Approvals)
        let mut items: Vec<ListItem> = app
            .queues
            .iter()
            .map(|q| ListItem::new(Line::from(vec![Span::raw(q)])))
            .collect();
        if !app.approvals.is_empty() {
            items.push(ListItem::new(Line::from("Approvals:")));
            for a in &app.approvals { items.push(ListItem::new(Line::from(a.as_str()))); }
        }
        let title = format!("Queues ⟳{}", ["⠁","⠃","⠇","⠋"][app.spinner]);
        let sidebar = List::new(items).block(Block::default().borders(Borders::ALL).title(title));
        f.render_widget(sidebar, main_layout[idx]);
        idx += 1;
    }

    // Chat (with scrollback)
    let mut chat_lines: Vec<Line> = app.chat.iter().map(|l| Line::from(l.as_str())).collect();
    let overflow = app.chat_scroll.min(chat_lines.len());
    if overflow > 0 { chat_lines.insert(0, Line::from(Span::styled(format!("[scroll +{}]", overflow), Style::default().fg(Color::DarkGray)))); }
    let chat = Paragraph::new(chat_lines)
        .block(Block::default().borders(Borders::ALL).title("Chat"))
        .wrap(Wrap { trim: true })
        .scroll((app.chat_scroll as u16, 0));
    f.render_widget(chat, main_layout[idx]);
    idx += 1;

    if app.show_backlog {
        // Backlog
        let backlog_items: Vec<ListItem> = app
            .backlog
            .iter()
            .map(|b| ListItem::new(Line::from(b.as_str())))
            .collect();
        let backlog = List::new(backlog_items).block(Block::default().borders(Borders::ALL).title("Backlog"));
        f.render_widget(backlog, main_layout[idx]);
    }

    // Input
    let mode = if app.input_mode { "(cmd)" } else { "(press : to command)" };
    let input = Paragraph::new(Line::from(vec![
        Span::styled(": ", Style::default().fg(Color::LightBlue)),
        Span::raw(&app.input),
        Span::raw(" "),
        Span::styled(mode, Style::default().fg(Color::DarkGray)),
    ]))
    .block(Block::default().borders(Borders::ALL).title("Input"));
    f.render_widget(input, chunks[1]);

    // Logs/Status
    if app.show_logs {
        let mut lines: Vec<Line> = app.logs.iter().rev().take(3).rev().map(|l| Line::from(l.as_str())).collect();
        lines.push(Line::from(Span::styled(app.status.as_str(), Style::default().fg(Color::LightGreen))));
        let logs = Paragraph::new(lines).block(Block::default().borders(Borders::ALL).title("Logs"));
        f.render_widget(logs, chunks[2]);
    } else {
        let status = Paragraph::new(app.status.as_str()).block(Block::default().borders(Borders::ALL).title("Status"));
        f.render_widget(status, chunks[2]);
    }
}

async fn spawn_cmd(cmdline: String, tx: mpsc::UnboundedSender<AppEvent>) -> Result<()> {
    // Recognize a few convenience commands and route to ocean CLI
    let (program, args): (String, Vec<String>) = if cmdline.starts_with("prd:") {
        let text = cmdline.splitn(2, ':').nth(1).unwrap_or("").trim().to_string();
        // write PRD and plan
        tokio::fs::write("docs/prd.md", format!("{}\n", text)).await.ok();
        ("ocean".into(), vec!["chat".into(), "--stage=false".into()])
    } else if cmdline == "plan" {
        ("ocean".into(), vec!["clarify".into()])
    } else if cmdline == "build" {
        ("ocean".into(), vec!["chat".into(), "--stage=false".into()])
    } else if cmdline == "stage" || cmdline == "deploy" {
        ("ocean".into(), vec!["deploy".into(), "--no-dry-run".into()])
    } else if cmdline.starts_with("release") {
        // support: release [--push] [--tag X]
        let extra = cmdline.split_whitespace().skip(1).map(|s| s.to_string()).collect::<Vec<_>>();
        let mut v = vec!["release".into()];
        v.extend(extra);
        ("ocean".into(), v)
    } else {
        ("sh".into(), vec!["-lc".into(), cmdline])
    };

    let mut child = Command::new(program)
        .args(args.clone())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .with_context(|| format!("failed spawning command"))?;

    let stdout = child.stdout.take().unwrap();
    let stderr = child.stderr.take().unwrap();
    let mut r_out = BufReader::new(stdout).lines();
    let mut r_err = BufReader::new(stderr).lines();
    let tx_out = tx.clone();
    tokio::spawn(async move {
        while let Ok(Some(line)) = r_out.next_line().await {
            let _ = tx_out.send(AppEvent::AppendChat(line));
        }
    });
    let tx_err = tx.clone();
    tokio::spawn(async move {
        while let Ok(Some(line)) = r_err.next_line().await {
            let _ = tx_err.send(AppEvent::AppendChat(format!("[stderr] {}", line)));
        }
    });

    let status = child.wait().await?;
    let _ = tx.send(AppEvent::SetStatus(format!(
        "Command exited with status {}",
        status.code().unwrap_or(-1)
    )));
    Ok(())
}
