const { useState, useEffect, useRef, useMemo } = React;

const DBOT_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#5b8def",
  "theme": "dark",
  "density": "comfortable",
  "fontSans": "Inter",
  "sidebarWidth": 264
}/*EDITMODE-END*/;

// ───────────────────────────────────────────────────────────── seed data
const seedChats = [
  {
    id: "c1",
    title: "새 채팅",
    updatedAt: Date.now(),
    messages: [],
  }
];

const samplePrompts = [
  { icon: "users", title: "길드조회", sub: "길드 정보를 조회해 줘. 길드명: " },
  { icon: "trend", title: "결제내역", sub: "일주일간의 결제 내역을 보여줘" },
  { icon: "search", title: "사용자 조회", sub: "사용자를 조회해 줘. 닉네임: " },
  { icon: "code", title: "쿠폰 사용내역", sub: "쿠폰 사용내역을 조회해 줘. 쿠폰번호: " },
];

function hoursAgo(h) { return Date.now() - h * 3600_000; }
function daysAgo(d) { return Date.now() - d * 86400_000; }

function groupByDate(chats) {
  const buckets = { today: [], yesterday: [], week: [], older: [] };
  const now = Date.now();
  for (const c of chats) {
    const ageH = (now - c.updatedAt) / 3600_000;
    if (ageH < 24) buckets.today.push(c);
    else if (ageH < 48) buckets.yesterday.push(c);
    else if (ageH < 168) buckets.week.push(c);
    else buckets.older.push(c);
  }
  return [
    { label: "오늘", items: buckets.today },
    { label: "어제", items: buckets.yesterday },
    { label: "지난 7일", items: buckets.week },
    { label: "이전", items: buckets.older },
  ].filter(g => g.items.length);
}

// ───────────────────────────────────────────────────────────── icons
const Icon = ({ name, size = 16 }) => {
  const s = { width: size, height: size, fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "plus": return (<svg viewBox="0 0 24 24" {...s}><path d="M12 5v14M5 12h14" /></svg>);
    case "search": return (<svg viewBox="0 0 24 24" {...s}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>);
    case "send": return (<svg viewBox="0 0 24 24" {...s}><path d="M5 12h14M13 6l6 6-6 6" /></svg>);
    case "db": return (<svg viewBox="0 0 24 24" {...s}><ellipse cx="12" cy="5.5" rx="7" ry="2.5" /><path d="M5 5.5v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6" /><path d="M5 11.5v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6" /></svg>);
    case "trend": return (<svg viewBox="0 0 24 24" {...s}><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg>);
    case "users": return (<svg viewBox="0 0 24 24" {...s}><circle cx="9" cy="9" r="3.2" /><path d="M3 19c.6-3 3.2-4.6 6-4.6s5.4 1.6 6 4.6" /><circle cx="17" cy="8" r="2.4" /><path d="M15.5 14.4c2.5.2 4.5 1.7 5.5 4.6" /></svg>);
    case "alert": return (<svg viewBox="0 0 24 24" {...s}><path d="M12 4l9 16H3z" /><path d="M12 10v5" /><circle cx="12" cy="17.6" r=".4" fill="currentColor" /></svg>);
    case "stack": return (<svg viewBox="0 0 24 24" {...s}><path d="M4 7l8-3 8 3-8 3-8-3z" /><path d="M4 12l8 3 8-3" /><path d="M4 17l8 3 8-3" /></svg>);
    case "more": return (<svg viewBox="0 0 24 24" {...s}><circle cx="5" cy="12" r=".8" fill="currentColor" /><circle cx="12" cy="12" r=".8" fill="currentColor" /><circle cx="19" cy="12" r=".8" fill="currentColor" /></svg>);
    case "trash": return (<svg viewBox="0 0 24 24" {...s}><path d="M4 7h16M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" /><path d="M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13" /></svg>);
    case "edit": return (<svg viewBox="0 0 24 24" {...s}><path d="M4 20h4l10-10-4-4L4 16z" /><path d="M14 6l4 4" /></svg>);
    case "panel": return (<svg viewBox="0 0 24 24" {...s}><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /></svg>);
    case "spark": return (<svg viewBox="0 0 24 24" {...s}><path d="M12 3l1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6z" /></svg>);
    case "table": return (<svg viewBox="0 0 24 24" {...s}><rect x="3" y="4" width="18" height="16" rx="1.5" /><path d="M3 10h18M3 16h18M9 4v16M15 4v16" /></svg>);
    case "code": return (<svg viewBox="0 0 24 24" {...s}><path d="m9 8-5 4 5 4M15 8l5 4-5 4" /></svg>);
    case "copy": return (<svg viewBox="0 0 24 24" {...s}><rect x="8" y="8" width="12" height="12" rx="1.6" /><path d="M16 8V5.6A1.6 1.6 0 0 0 14.4 4H5.6A1.6 1.6 0 0 0 4 5.6v8.8A1.6 1.6 0 0 0 5.6 16H8" /></svg>);
    case "check": return (<svg viewBox="0 0 24 24" {...s}><path d="m5 12 4 4 10-10" /></svg>);
    default: return null;
  }
};

// ───────────────────────────────────────────────────────────── sidebar
function Sidebar({ chats, activeId, onSelect, onNew, onDelete, collapsed, onToggle, width, servers, serverId, onServerChange }) {
  const groups = useMemo(() => groupByDate(chats), [chats]);
  if (collapsed) {
    return (
      <aside className="db-sidebar db-sidebar--collapsed">
        <button className="db-iconbtn" onClick={onToggle} title="사이드바 열기"><Icon name="panel" /></button>
        <button className="db-iconbtn db-iconbtn--accent" onClick={onNew} title="새 채팅"><Icon name="plus" /></button>
      </aside>
    );
  }
  return (
    <aside className="db-sidebar" style={{ width }}>
      <div className="db-sidebar__head">
        <div className="db-brand">
          <span className="db-brand__mark"><Icon name="db" size={18} /></span>
          <span className="db-brand__name">DBot</span>
        </div>
        <button className="db-iconbtn" onClick={onToggle} title="접기"><Icon name="panel" /></button>
      </div>

      <button className="db-newchat" onClick={onNew}>
        <Icon name="plus" size={15} />
        <span>새 채팅</span>
      </button>

      <div className="db-search">
        <Icon name="search" size={14} />
        <input placeholder="채팅 검색..." />
      </div>

      <nav className="db-chatlist">
        {groups.map(g => (
          <section className="db-chatgroup" key={g.label}>
            <h4 className="db-chatgroup__label">{g.label}</h4>
            <ul>
              {g.items.map(c => (
                <li
                  key={c.id}
                  className={"db-chatitem" + (c.id === activeId ? " db-chatitem--active" : "")}
                  onClick={() => onSelect(c.id)}
                >
                  <span className="db-chatitem__title">{c.title}</span>
                  <button
                    className="db-chatitem__del"
                    onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}
                    title="삭제"
                  >
                    <Icon name="trash" size={14} />
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
        {groups.length === 0 && (
          <div className="db-empty-list">아직 채팅이 없어요</div>
        )}
      </nav>

      <div className="db-sidebar__foot">
        <div className="db-conn">
          <span className="db-conn__dot" />
          <div className="db-conn__meta">
            <div className="db-conn__name">
              <select value={serverId} onChange={(e) => onServerChange(e.target.value)} style={{ background: 'transparent', border: 'none', color: 'inherit', font: 'inherit', outline: 'none', cursor: 'pointer', padding: 0 }}>
                {servers && servers.map(s => <option key={s.id} value={s.id} style={{ color: 'black' }}>{s.name}</option>)}
                {(!servers || servers.length === 0) && <option value="default">기본 서버</option>}
              </select>
            </div>
            <div className="db-conn__sub">읽기 전용</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

// ───────────────────────────────────────────────────────────── messages + results
function ResultBlock({ msg }) {
  const [tab, setTab] = useState("table");
  const [copied, setCopied] = useState(false);
  if (!msg.sql && !msg.rows) return null;

  const cols = msg.rows && msg.rows.length ? Object.keys(msg.rows[0]) : [];
  const fmt = (v) => typeof v === "number" ? v.toLocaleString() : String(v);

  const copy = () => {
    navigator.clipboard?.writeText(msg.sql || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  return (
    <div className="db-result">
      <div className="db-result__head">
        <div className="db-tabs">
          <button className={"db-tab" + (tab === "table" ? " db-tab--on" : "")} onClick={() => setTab("table")}>
            <Icon name="table" size={13} /> 결과 {msg.rows ? `(${msg.rows.length})` : ""}
          </button>
          <button className={"db-tab" + (tab === "sql" ? " db-tab--on" : "")} onClick={() => setTab("sql")}>
            <Icon name="code" size={13} /> SQL
          </button>
        </div>
        <div className="db-result__meta">
          {msg.ms && <span>{msg.ms} ms</span>}
          <button className="db-iconbtn db-iconbtn--ghost" onClick={copy} title="SQL 복사">
            <Icon name={copied ? "check" : "copy"} size={13} />
          </button>
        </div>
      </div>

      {tab === "sql" && (
        <pre className="db-sql"><code>{msg.sql}</code></pre>
      )}
      {tab === "table" && msg.rows && (
        <div className="db-table-wrap">
          <table className="db-table">
            <thead>
              <tr>{cols.map(c => <th key={c}>{c}</th>)}</tr>
            </thead>
            <tbody>
              {msg.rows.map((r, i) => (
                <tr key={i}>{cols.map(c => <td key={c} className={typeof r[c] === "number" ? "num" : ""}>{fmt(r[c])}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Message({ msg }) {
  if (msg.role === "user") {
    return (
      <div className="db-msg db-msg--user">
        <div className="db-bubble">{msg.text}</div>
      </div>
    );
  }
  return (
    <div className="db-msg db-msg--asst">
      <div className="db-asst">
        <div className="db-asst__avatar"><Icon name="db" size={14} /></div>
        <div className="db-asst__body">
          <div className="db-asst__text">{msg.text}</div>
          <ResultBlock msg={msg} />
        </div>
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────── empty state
function EmptyState({ onPick }) {
  return (
    <div className="db-empty">
      <div className="db-empty__mark"><Icon name="db" size={28} /></div>
      <h1 className="db-empty__h1">무엇을 조회해 드릴까요?</h1>
      <p className="db-empty__sub">자연어로 질문하면 SQL을 생성하고 결과를 보여드립니다.</p>

      <div className="db-prompts">
        {samplePrompts.map(p => (
          <button key={p.title} className="db-prompt" onClick={() => onPick(p.sub)}>
            <span className="db-prompt__icon"><Icon name={p.icon} size={15} /></span>
            <span className="db-prompt__title">{p.title}</span>
            <span className="db-prompt__sub">{p.sub}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────── composer
function Composer({ onSend, value, onChange, busy, servers, serverId }) {
  const ta = useRef(null);
  useEffect(() => {
    const el = ta.current; if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 220) + "px";
  }, [value]);

  const submit = () => {
    const v = value.trim();
    if (!v || busy) return;
    onSend(v);
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <div className="db-composer">
      <div className="db-composer__inner">
        <textarea
          ref={ta}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={onKey}
          rows={1}
          placeholder="DB에 질문하세요. 예: 어제 결제 완료된 주문 수"
        />
        <div className="db-composer__row">
          <div className="db-composer__hint">
            <Icon name="spark" size={12} />
            <span>{servers && servers.find(s => s.id === serverId)?.name || '기본 서버'}</span>
            <span className="db-dot">·</span>
            <span>읽기 전용</span>
          </div>
          <button
            className="db-send"
            onClick={submit}
            disabled={!value.trim() || busy}
            title="전송 (Enter)"
          >
            {busy ? <span className="db-spinner" /> : <Icon name="send" size={15} />}
          </button>
        </div>
      </div>
      <div className="db-foothint">DBot은 실수할 수 있습니다. 중요한 데이터는 담당자에게 한번 더 확인해주세요!</div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────── app
function App() {
  const [t, setTweak] = window.useTweaks(DBOT_DEFAULTS);
  const [chats, setChats] = useState(() => {
    try {
      const saved = localStorage.getItem("dbot_chats");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.length > 0) return parsed;
      }
    } catch (e) { }
    return seedChats;
  });
  const [activeId, setActiveId] = useState(() => {
    try {
      const saved = localStorage.getItem("dbot_active_id");
      if (saved) return saved;
    } catch (e) { }
    return seedChats[0].id;
  });

  useEffect(() => {
    localStorage.setItem("dbot_chats", JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    if (activeId) {
      localStorage.setItem("dbot_active_id", activeId);
    } else {
      localStorage.removeItem("dbot_active_id");
    }
  }, [activeId]);

  const [servers, setServers] = useState([]);
  const [serverId, setServerId] = useState(() => {
    try {
      const saved = localStorage.getItem("dbot_server_id");
      if (saved) return saved;
    } catch (e) { }
    return "default";
  });

  useEffect(() => {
    fetch('/servers').then(res => res.json()).then(data => {
      setServers(data);
      if (data.length > 0 && !data.find(s => s.id === serverId)) {
        setServerId(data[0].id);
      }
    }).catch(err => console.error(err));
  }, []);

  useEffect(() => {
    localStorage.setItem("dbot_server_id", serverId);
  }, [serverId]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const scrollRef = useRef(null);

  const active = chats.find(c => c.id === activeId);

  // apply tweaks via CSS vars
  useEffect(() => {
    const r = document.documentElement;
    r.style.setProperty("--accent", t.accent);
    r.dataset.theme = t.theme;
    r.dataset.density = t.density;
    r.style.setProperty("--font-sans",
      t.fontSans === "Inter" ? `"Inter", system-ui, sans-serif`
        : t.fontSans === "JetBrains" ? `"JetBrains Mono", ui-monospace, monospace`
          : t.fontSans === "Geist" ? `"Geist", system-ui, sans-serif`
            : `system-ui, sans-serif`);
  }, [t]);

  // autoscroll on new message
  useEffect(() => {
    const el = scrollRef.current; if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [active?.messages?.length, busy]);



  const handleNew = () => {
    const id = "c" + Math.random().toString(36).slice(2, 8);
    const c = { id, title: "새 채팅", updatedAt: Date.now(), messages: [] };
    setChats(prev => [c, ...prev]);
    setActiveId(id);
    setDraft("");
  };

  const handleDelete = (id) => {
    setChats(prev => {
      const next = prev.filter(c => c.id !== id);
      if (id === activeId) setActiveId(next[0]?.id || null);
      return next;
    });
  };

  const handleSend = async (text) => {
    let currentActive = active;
    let newChats = [...chats];
    if (!currentActive) {
      const id = "c" + Math.random().toString(36).slice(2, 8);
      currentActive = { id, title: text.slice(0, 28), updatedAt: Date.now(), messages: [] };
      newChats = [currentActive, ...newChats];
      setActiveId(id);
    }

    setBusy(true);
    setChats(newChats.map(c => c.id === currentActive.id
      ? {
        ...c,
        title: c.messages.length === 0 ? text.slice(0, 28) : c.title,
        updatedAt: Date.now(),
        messages: [...c.messages, { role: "user", text }]
      }
      : c));
    setDraft("");

    try {
      const startTime = Date.now();
      const response = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, session_id: currentActive.id, server_id: serverId })
      });
      const data = await response.json();
      const ms = Date.now() - startTime;

      let reply;
      if (response.ok) {
        reply = {
          role: "assistant",
          text: "결과를 가져왔습니다.",
          sql: data.sql,
          rows: data.result,
          ms: ms,
        };
      } else {
        reply = {
          role: "assistant",
          text: `오류가 발생했습니다: ${data.detail?.error || data.error || '알 수 없는 오류'}`,
          ms: ms,
        };
      }

      setChats(prev => prev.map(c => c.id === active.id
        ? { ...c, updatedAt: Date.now(), messages: [...c.messages, reply] }
        : c));
    } catch (err) {
      setChats(prev => prev.map(c => c.id === active.id
        ? { ...c, updatedAt: Date.now(), messages: [...c.messages, { role: "assistant", text: "네트워크 오류가 발생했습니다." }] }
        : c));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="db-app">
      <Sidebar
        chats={chats}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNew}
        onDelete={handleDelete}
        collapsed={collapsed}
        onToggle={() => setCollapsed(c => !c)}
        servers={servers}
        serverId={serverId}
        onServerChange={setServerId}
        width={t.sidebarWidth}
      />

      <main className="db-main">
        <header className="db-topbar">
          <div className="db-topbar__title">
            {active ? active.title : "새 채팅"}
          </div>
          <div className="db-topbar__meta">
            <span className="db-pill"><span className="db-pill__dot" /> production</span>
          </div>
        </header>

        <div className="db-scroll" ref={scrollRef}>
          {!active || active.messages.length === 0 ? (
            <EmptyState onPick={(s) => setDraft(s)} />
          ) : (
            <div className="db-thread">
              {active.messages.map((m, i) => <Message key={i} msg={m} />)}
              {busy && (
                <div className="db-msg db-msg--asst">
                  <div className="db-asst">
                    <div className="db-asst__avatar"><Icon name="db" size={14} /></div>
                    <div className="db-asst__body">
                      <div className="db-typing"><span /><span /><span /></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <Composer onSend={handleSend} value={draft} onChange={setDraft} busy={busy} servers={servers} serverId={serverId} />
      </main>

      <DBotTweaks t={t} setTweak={setTweak} />
    </div>
  );
}

function DBotTweaks({ t, setTweak }) {
  const { TweaksPanel, TweakSection, TweakRadio, TweakSlider, TweakColor, TweakSelect } = window;
  return (
    <TweaksPanel title="Tweaks">
      <TweakSection title="Theme">
        <TweakRadio label="Mode" value={t.theme} onChange={(v) => setTweak("theme", v)}
          options={[{ value: "dark", label: "Dark" }, { value: "light", label: "Light" }]} />
        <TweakColor label="Accent" value={t.accent} onChange={(v) => setTweak("accent", v)}
          options={["#5b8def", "#3ecf8e", "#c084fc", "#f59e0b", "#f87171"]} />
      </TweakSection>
      <TweakSection title="Layout">
        <TweakRadio label="Density" value={t.density} onChange={(v) => setTweak("density", v)}
          options={[{ value: "compact", label: "Compact" }, { value: "comfortable", label: "Comfort" }]} />
        <TweakSlider label="Sidebar width" value={t.sidebarWidth} min={220} max={340} step={4}
          onChange={(v) => setTweak("sidebarWidth", v)} />
      </TweakSection>
      <TweakSection title="Type">
        <TweakSelect label="Sans font" value={t.fontSans} onChange={(v) => setTweak("fontSans", v)}
          options={[
            { value: "Inter", label: "Inter" },
            { value: "Geist", label: "Geist" },
            { value: "system", label: "System" },
          ]} />
      </TweakSection>
    </TweaksPanel>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
