import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowDownToLine, ArrowLeftRight, ArrowRight, Bell,
  Check, CheckCircle2, ChevronDown, ChevronLeft, ChevronRight,
  CircleAlert, Clock3, CloudUpload, Database, FileSpreadsheet,
  FileText, Gauge, History, LayoutDashboard, LoaderCircle, Menu,
  RefreshCw, Search, ShieldCheck, SlidersHorizontal, Sparkles,
  Upload, X, XCircle, Zap
} from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis
} from "recharts";
import "./App.css";

const API = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

const navigation = [
  { id: "dashboard", label: "Panel de control", icon: LayoutDashboard, section: "PLATAFORMA" },
  { id: "reconcile", label: "Nueva reconciliación", icon: ArrowLeftRight },
  { id: "history", label: "Historial de ejecuciones", icon: History },
  { id: "quality", label: "Calidad de datos", icon: ShieldCheck, section: "ANÁLISIS" },
];

const checkLabels = {
  RECORD_COUNTS: "Volumen de registros",
  MISSING_RECORDS: "Registros faltantes",
  UNEXPECTED_RECORDS: "Registros inesperados",
  FIELD_DIFFERENCES: "Diferencias entre campos",
  DUPLICATE_KEYS: "Claves duplicadas",
  BLANK_KEYS: "Claves vacías",
  SCHEMA: "Compatibilidad del esquema",
};

const prettyDate = (value) => {
  if (!value) return "Fecha no disponible";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
};

const number = (value) => Number(value || 0).toLocaleString("es-CO");


function getSummary(run) {
  return run?.summary || run?.result?.summary || run?.data?.summary || {};
}





function downloadFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
}

function exportResultJson(result) {
  if (!result) {
    console.error("No hay resultados para exportar.");
    return;
  }

  const filename = `migravalid-${getRunId(result)}.json`;

  downloadFile(
    filename,
    JSON.stringify(result, null, 2),
    "application/json;charset=utf-8"
  );
}

function exportDifferencesCsv(result) {
  if (!result) {
    console.error("No hay resultados para exportar.");
    return;
  }

  const checks =
    result?.checks ||
    result?.result?.checks ||
    result?.data?.checks ||
    [];

  const differencesCheck = checks.find(
    (check) => check.name === "FIELD_DIFFERENCES"
  );

  const differences = differencesCheck?.items || [];

  const rows = [
    ["Clave", "Columna", "Valor origen", "Valor destino"],
    ...differences.map((item) => [
      item.key,
      item.column,
      item.source_value,
      item.target_value,
    ]),
  ];

  const csv = rows
    .map((row) =>
      row
        .map((value) => {
          const safe = String(value ?? "");
          return `"${safe.replace(/"/g, '""')}"`;
        })
        .join(",")
    )
    .join("\r\n");

  downloadFile(
    `migravalid-diferencias-${getRunId(result)}.csv`,
    "\uFEFF" + csv,
    "text/csv;charset=utf-8"
  );
}


function getStatus(run) {
  const value = String(run?.status || run?.result?.status || run?.result_status || "").toUpperCase();
  if (["PASS", "SUCCESS", "SUCCEEDED", "COMPLETED"].includes(value)) return "PASS";
  if (["FAIL", "FAILED", "ERROR"].includes(value)) return "FAIL";
  return value || "UNKNOWN";
}

function getRunId(run) {
  return run?.run_id ?? run?.id ?? run?.execution_id ?? "—";
}

function getRunDate(run) {
  return run?.created_at ?? run?.createdAt ?? run?.started_at ?? run?.timestamp;
}

function StatusPill({ status }) {
  const pass = status === "PASS";
  const fail = status === "FAIL";
  return (
    <span className={`status-pill ${pass ? "status-pass" : fail ? "status-fail" : "status-neutral"}`}>
      <span className="status-dot" />
      {pass ? "Aprobado" : fail ? "Con diferencias" : status === "UNKNOWN" ? "Sin estado" : status}
    </span>
  );
}

function MetricCard({ label, value, detail, icon: Icon, tone = "cyan" }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon metric-${tone}`}><Icon size={19} /></div>
      <p className="metric-label">{label}</p>
      <div className="metric-value">{value}</div>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}

function EmptyState({ icon: Icon = FileSpreadsheet, title, detail, action, onAction }) {
  return (
    <div className="empty-state">
      <div className="empty-icon"><Icon size={25} /></div>
      <h3>{title}</h3>
      <p>{detail}</p>
      {action && <button className="button button-primary" onClick={onAction}>{action}<ArrowRight size={16} /></button>}
    </div>
  );
}

function App() {
  const [view, setView] = useState("dashboard");
  const [health, setHealth] = useState("checking");
  const [runs, setRuns] = useState([]);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [apiError, setApiError] = useState("");
  const [mobileNav, setMobileNav] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const [search, setSearch] = useState("");
  const [sourceFile, setSourceFile] = useState(null);
  const [targetFile, setTargetFile] = useState(null);
  const [keyColumn, setKeyColumn] = useState("id");
  const [busy, setBusy] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [result, setResult] = useState(null);
  const [dragTarget, setDragTarget] = useState("");

  const loadData = useCallback(async () => {
    setLoadingRuns(true);
    setApiError("");
    try {
      const healthResponse = await fetch(`${API}/api/v1/health`);
      if (!healthResponse.ok) throw new Error(`La API respondió HTTP ${healthResponse.status}`);
      setHealth("online");
      const runsResponse = await fetch(`${API}/api/v1/runs?limit=100&offset=0`);
      if (!runsResponse.ok) throw new Error(`No se pudo consultar el historial (HTTP ${runsResponse.status})`);
      const payload = await runsResponse.json();
      setRuns(Array.isArray(payload) ? payload : Array.isArray(payload.items) ? payload.items : []);
    } catch (error) {
      setHealth("offline");
      setApiError(error.message || "No fue posible conectar con la API.");
      setRuns([]);
    } finally {
      setLoadingRuns(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const stats = useMemo(() => {
    const completed = runs.filter((run) => ["PASS", "FAIL"].includes(getStatus(run)));
    const passed = completed.filter((run) => getStatus(run) === "PASS").length;
    const failed = completed.filter((run) => getStatus(run) === "FAIL").length;
    const sourceRows = runs.reduce((sum, run) => sum + Number(getSummary(run).source_rows || 0), 0);
    const targetRows = runs.reduce((sum, run) => sum + Number(getSummary(run).target_rows || 0), 0);
    return { total: runs.length, passed, failed, sourceRows, targetRows };
  }, [runs]);

  const chartData = useMemo(() => {
    return [...runs]
      .filter((run) => getRunDate(run))
      .sort((a, b) => new Date(getRunDate(a)) - new Date(getRunDate(b)))
      .slice(-8)
      .map((run) => ({
        name: new Date(getRunDate(run)).toLocaleDateString("es-CO", { day: "2-digit", month: "short" }),
        aprobadas: getStatus(run) === "PASS" ? 1 : 0,
        conDiferencias: getStatus(run) === "FAIL" ? 1 : 0,
      }));
  }, [runs]);

  const filteredRuns = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return runs;
    return runs.filter((run) => {
      const summary = getSummary(run);
      return [
        getRunId(run), getStatus(run), getRunDate(run),
        summary.source_file, summary.target_file, summary.key_column
      ].some((value) => String(value ?? "").toLowerCase().includes(term));
    });
  }, [runs, search]);

  const navigate = (nextView) => {
    setView(nextView);
    setMobileNav(false);
    setSelectedRun(null);
    if (nextView !== "reconcile") setResult(null);
  };

  const pickFile = (file, side) => {
    if (!file) return;
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!["csv", "xlsx"].includes(extension)) {
      setUploadError("Formato no admitido. Selecciona un archivo CSV o XLSX.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("El archivo supera el límite de 10 MB.");
      return;
    }
    setUploadError("");
    if (side === "source") setSourceFile(file);
    else setTargetFile(file);
  };

  const runReconciliation = async (event) => {
    event.preventDefault();
    setUploadError("");
    setResult(null);
    if (!sourceFile || !targetFile) {
      setUploadError("Selecciona los dos archivos antes de ejecutar la reconciliación.");
      return;
    }
    if (!keyColumn.trim()) {
      setUploadError("Escribe el nombre de la columna clave, por ejemplo: id.");
      return;
    }

    const body = new FormData();
    body.append("source_file", sourceFile);
    body.append("target_file", targetFile);
    body.append("key_column", keyColumn.trim());
    setBusy(true);
    try {
      const response = await fetch(`${API}/api/v1/reconciliation/files`, { method: "POST", body });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || payload.message || `La reconciliación falló (HTTP ${response.status}).`);
      setResult(payload);
      await loadData();
    } catch (error) {
      setUploadError(error.message || "No fue posible ejecutar la reconciliación.");
    } finally {
      setBusy(false);
    }
  };

  const openRun = async (run) => {
    setSelectedRun(run);
    setView("history");
    const id = getRunId(run);
    if (id === "—") return;
    try {
      const response = await fetch(`${API}/api/v1/runs/${encodeURIComponent(id)}`);
      if (response.ok) setSelectedRun(await response.json());
    } catch {
      // Se conserva el registro ya disponible en el historial.
    }
  };

  const currentTitle = {
    dashboard: ["Panel de control", "Resumen operativo de tus validaciones de datos."],
    reconcile: ["Nueva reconciliación", "Compara dos archivos y encuentra diferencias con precisión."],
    history: ["Historial de ejecuciones", "Consulta los resultados registrados en PostgreSQL."],
    quality: ["Calidad de datos", "Las siete validaciones que ejecuta el motor de reconciliación."],
  }[view] || ["MIGRAVALID QA", "Plataforma de integridad de datos."];

  return (
    <div className="app-shell">
      {mobileNav && <button className="mobile-scrim" aria-label="Cerrar menú" onClick={() => setMobileNav(false)} />}
      <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><ArrowLeftRight size={22} strokeWidth={2.4} /></div>
          <div><div className="brand-name">MIGRA<span>VALID</span></div><div className="brand-caption">DATA QUALITY PLATFORM</div></div>
          <button className="mobile-close" onClick={() => setMobileNav(false)} aria-label="Cerrar menú"><X size={18} /></button>
        </div>
        <div className="workspace-switch">
          <div className="workspace-avatar">DQ</div>
          <div className="workspace-copy"><strong>Data Quality Lab</strong><span>Espacio de trabajo</span></div>
          <ChevronDown size={15} className="muted-icon" />
        </div>
        <nav className="main-nav">
          {navigation.map((item) => (
            <div key={item.id}>
              {item.section && <div className="nav-section">{item.section}</div>}
              <button className={`nav-item ${view === item.id ? "nav-active" : ""}`} onClick={() => navigate(item.id)}>
                <item.icon size={18} strokeWidth={1.8} /><span>{item.label}</span>
                {item.id === "reconcile" && <span className="nav-plus">+</span>}
              </button>
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="api-status">
            <span className={`pulse-dot ${health === "online" ? "pulse-online" : health === "offline" ? "pulse-offline" : ""}`} />
            <div><strong>Servicio de API</strong><span>{health === "online" ? "Conectado" : health === "offline" ? "Sin conexión" : "Verificando..."}</span></div>
            <span className={`api-status-label ${health === "online" ? "online-label" : ""}`}>{health === "online" ? "LIVE" : "API"}</span>
          </div>
          <div className="sidebar-footer"><span>DATA ENGINE</span><span>v0.1.0</span></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu" onClick={() => setMobileNav(true)} aria-label="Abrir menú"><Menu size={20} /></button>
            <div className="breadcrumb">Workspace <ChevronRight size={14} /> <span>{currentTitle[0]}</span></div>
          </div>
          <div className="topbar-right">
            <span className={`connection-tag ${health === "online" ? "connection-good" : ""}`}><span className="status-dot" />{health === "online" ? "API conectada" : health === "checking" ? "Conectando" : "API desconectada"}</span>
            <button className="icon-button" title="Actualizar datos" onClick={loadData}><RefreshCw size={17} /></button>
            <div className="user-avatar" title="Data Quality Lab">DQ</div>
          </div>
        </header>

        <div className="page-content">
          {apiError && (
            <div className="alert alert-error"><CircleAlert size={18} /><div><strong>No se puede conectar con el backend</strong><p>{apiError} Comprueba que FastAPI esté activo en <code>http://localhost:8000</code>.</p></div><button onClick={loadData} className="alert-retry">Reintentar</button></div>
          )}

          <div className="page-heading">
            <div><div className="eyebrow"><span className="eyebrow-line" />DATA OPERATIONS</div><h1>{currentTitle[0]}</h1><p>{currentTitle[1]}</p></div>
            {view !== "reconcile" && <button className="button button-primary" onClick={() => navigate("reconcile")}><Zap size={16} /> Nueva reconciliación</button>}
          </div>

          {view === "dashboard" && (
            <>
              <section className="welcome-banner">
                <div className="welcome-orb orb-one" /><div className="welcome-orb orb-two" />
                <div className="welcome-copy"><div className="banner-kicker"><Sparkles size={14} /> CENTRO DE CONTROL</div><h2>La confianza empieza<br />con <span>datos íntegros.</span></h2><p>Detecta inconsistencias, valida migraciones y mantén tus datos bajo control.</p><button className="banner-button" onClick={() => navigate("reconcile")}>Iniciar validación <ArrowRight size={16} /></button></div>
                <div className="banner-visual"><div className="visual-ring ring-large" /><div className="visual-ring ring-small" /><div className="visual-core"><ShieldCheck size={43} /></div><div className="visual-node node-top"><Database size={17} /></div><div className="visual-node node-bottom"><Check size={18} /></div><div className="visual-node node-right"><ArrowLeftRight size={17} /></div></div>
                <div className="banner-foot"><span><span className="live-dot" /> MOTOR DE VALIDACIÓN</span><span>CSV · XLSX · POSTGRESQL</span></div>
              </section>

              <div className="section-heading"><div><h2>Vista general</h2><p>Indicadores calculados a partir del historial disponible.</p></div><span className="period-label"><Activity size={14} /> Todas las ejecuciones</span></div>
              <section className="metrics-grid">
                <MetricCard label="Ejecuciones registradas" value={loadingRuns ? "—" : number(stats.total)} detail="En el historial consultado" icon={History} tone="cyan" />
                <MetricCard label="Validaciones aprobadas" value={loadingRuns ? "—" : number(stats.passed)} detail="Sin diferencias detectadas" icon={CheckCircle2} tone="green" />
                <MetricCard label="Con diferencias" value={loadingRuns ? "—" : number(stats.failed)} detail="Requieren revisión" icon={CircleAlert} tone="coral" />
                <MetricCard label="Filas procesadas" value={loadingRuns ? "—" : number(stats.sourceRows + stats.targetRows)} detail="Origen + destino, acumulado" icon={Database} tone="violet" />
              </section>

              <section className="dashboard-grid">
                <article className="panel chart-panel">
                  <div className="panel-heading"><div><h3>Actividad de validación</h3><p>Últimas ejecuciones con fecha registrada</p></div><div className="chart-legend"><span><i className="legend-green" />Aprobadas</span><span><i className="legend-coral" />Con diferencias</span></div></div>
                  {chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}><defs><linearGradient id="passFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#35d6a0" stopOpacity={0.23} /><stop offset="95%" stopColor="#35d6a0" stopOpacity={0} /></linearGradient><linearGradient id="failFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ff7b86" stopOpacity={0.18} /><stop offset="95%" stopColor="#ff7b86" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#263342" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="name" tick={{ fill: "#8292a5", fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis allowDecimals={false} tick={{ fill: "#8292a5", fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: "#111c29", border: "1px solid #2b3a4b", borderRadius: 10, color: "#eaf0f7", fontSize: 12 }} /><Area type="monotone" dataKey="aprobadas" name="Aprobadas" stroke="#35d6a0" fill="url(#passFill)" strokeWidth={2.5} /><Area type="monotone" dataKey="conDiferencias" name="Con diferencias" stroke="#ff7b86" fill="url(#failFill)" strokeWidth={2.5} /></AreaChart></ResponsiveContainer></div> : <EmptyState icon={Activity} title="Aún no hay actividad" detail="Cuando ejecutes reconciliaciones, aquí aparecerá la actividad registrada." action="Ejecutar primera validación" onAction={() => navigate("reconcile")} />}
                </article>
                <article className="panel integrity-panel">
                  <div className="panel-heading"><div><h3>Integridad del sistema</h3><p>Estado de los servicios</p></div><Gauge size={19} className="muted-icon" /></div>
                  <div className="integrity-status"><div className={`integrity-icon ${health === "online" ? "integrity-ok" : ""}`}>{health === "online" ? <CheckCircle2 size={25} /> : health === "offline" ? <XCircle size={25} /> : <LoaderCircle size={25} className="spin" />}</div><div><strong>{health === "online" ? "API disponible" : health === "offline" ? "API no disponible" : "Verificando servicios"}</strong><span>{health === "online" ? "Respuesta de salud recibida" : health === "offline" ? "Revisa el servidor FastAPI" : "Esperando respuesta del servidor"}</span></div></div>
                  <div className="service-row"><span><span className={`service-dot ${health === "online" ? "service-green" : ""}`} />API REST</span><strong>{health === "online" ? "Operativa" : health === "offline" ? "Desconectada" : "Verificando"}</strong></div>
                  <div className="service-row"><span><span className="service-dot service-blue" />Motor de reconciliación</span><strong>FastAPI</strong></div>
                  <div className="service-row"><span><span className="service-dot service-purple" />Persistencia</span><strong>PostgreSQL</strong></div>
                  <button className="text-button integrity-refresh" onClick={loadData}>Verificar de nuevo <ArrowRight size={15} /></button>
                </article>
              </section>

              <section className="panel recent-panel">
                <div className="panel-heading"><div><h3>Ejecuciones recientes</h3><p>Últimos resultados disponibles en el backend</p></div><button className="text-button" onClick={() => navigate("history")}>Ver historial completo <ArrowRight size={15} /></button></div>
                {loadingRuns ? <div className="loading-line"><LoaderCircle className="spin" size={18} /> Consultando historial...</div> : runs.length ? <RunTable runs={[...runs].sort((a, b) => new Date(getRunDate(b) || 0) - new Date(getRunDate(a) || 0)).slice(0, 5)} onOpen={openRun} /> : <EmptyState icon={History} title="Todavía no hay ejecuciones" detail="Los resultados aparecerán aquí cuando completes tu primera reconciliación." action="Crear reconciliación" onAction={() => navigate("reconcile")} />}
              </section>
            </>
          )}

          {view === "reconcile" && (
            <div className="reconcile-layout">
              <section className="panel upload-panel">
                <div className="panel-heading"><div><h3>Archivos para comparar</h3><p>Selecciona el origen y el destino de la migración.</p></div><span className="step-chip">PASO 01</span></div>
                <form onSubmit={runReconciliation}>
                  <div className="file-pair">
                    <FileDrop title="Archivo de origen" subtitle="Sistema de origen" file={sourceFile} onFile={(file) => pickFile(file, "source")} onClear={() => setSourceFile(null)} dragging={dragTarget === "source"} onDrag={(value) => setDragTarget(value ? "source" : "")} />
                    <div className="compare-arrow"><ArrowLeftRight size={20} /></div>
                    <FileDrop title="Archivo de destino" subtitle="Sistema migrado" file={targetFile} onFile={(file) => pickFile(file, "target")} onClear={() => setTargetFile(null)} dragging={dragTarget === "target"} onDrag={(value) => setDragTarget(value ? "target" : "")} />
                  </div>
                  <div className="file-rules"><ShieldCheck size={16} /><span>CSV o XLSX · máximo 10 MB por archivo · hasta 100.000 filas</span></div>
                  <div className="form-divider" />
                  <label className="field-label" htmlFor="key-column">Columna clave <span>OBLIGATORIA</span></label>
                  <p className="field-help">Campo que identifica de forma única cada registro y permite emparejar origen y destino.</p>
                  <div className="input-with-icon"><Database size={17} /><input id="key-column" value={keyColumn} onChange={(event) => setKeyColumn(event.target.value)} placeholder="Ej. id, customer_id, codigo" /><span className="input-suffix">KEY</span></div>
                  <div className="notice-box"><CircleAlert size={17} /><p>Los dos archivos deben contener la columna clave con el mismo nombre. Las diferencias se calcularán sobre las columnas compartidas.</p></div>
                  {uploadError && <div className="alert alert-error upload-alert"><CircleAlert size={17} /><span>{uploadError}</span></div>}
                  <div className="form-actions"><button type="button" className="button button-ghost" onClick={() => { setSourceFile(null); setTargetFile(null); setUploadError(""); setResult(null); }}>Limpiar archivos</button><button type="submit" className="button button-primary" disabled={busy}>{busy ? <><LoaderCircle size={17} className="spin" /> Analizando archivos...</> : <><Zap size={17} /> Ejecutar reconciliación <ArrowRight size={16} /></>}</button></div>
                </form>
              </section>
              <aside className="reconcile-aside">
                <article className="panel aside-panel"><div className="aside-icon"><ShieldCheck size={22} /></div><h3>Validaciones incluidas</h3><p>El motor ejecuta siete comprobaciones automáticas en cada comparación.</p><div className="checklist">{Object.entries(checkLabels).map(([key, label]) => <div key={key}><CheckCircle2 size={15} /><span>{label}</span></div>)}</div></article>
                <article className="panel aside-panel security-panel"><div className="aside-icon aside-icon-blue"><Database size={22} /></div><h3>Persistencia de resultados</h3><p>El resumen, las comprobaciones y las diferencias se guardan en PostgreSQL. Los archivos se procesan en memoria y no se almacenan.</p><div className="secure-foot"><ShieldCheck size={14} /> Procesamiento local en la API</div></article>
              </aside>
              {result && <section className="panel result-panel">
                <div className="panel-heading"><div><div className="eyebrow"><span className="eyebrow-line" />RESULTADO DE EJECUCIÓN</div><h3>Reconciliación completada</h3><p>Identificador: {result.run_id || "registrado"} · {prettyDate(result.created_at)}</p></div><StatusPill status={getStatus(result)} /></div>
                <ResultDetails result={result} />
                <div className="form-actions"><button className="button button-ghost" onClick={() => { setResult(null); setSourceFile(null); setTargetFile(null); }}>Nueva comparación</button><button className="button button-primary" onClick={() => { setSelectedRun(result); setView("history"); }}>Ver resultado <ArrowRight size={16} /></button></div>
              </section>}
            </div>
          )}

          {view === "history" && (
            <section className="panel history-panel">
              {selectedRun ? <RunDetail run={selectedRun} onBack={() => setSelectedRun(null)} /> : <>
                <div className="panel-heading history-heading"><div><h3>Todas las ejecuciones</h3><p>{runs.length} registro(s) devuelto(s) por la API</p></div><button className="button button-secondary" onClick={loadData}><RefreshCw size={15} /> Actualizar</button></div>
                <div className="table-toolbar"><div className="search-field"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por archivo, ID o estado..." /></div><span className="result-count">{filteredRuns.length} resultados</span></div>
                {loadingRuns ? <div className="loading-line"><LoaderCircle size={18} className="spin" /> Consultando historial...</div> : filteredRuns.length ? <RunTable runs={[...filteredRuns].sort((a, b) => new Date(getRunDate(b) || 0) - new Date(getRunDate(a) || 0))} onOpen={openRun} /> : <EmptyState icon={History} title={search ? "Sin coincidencias" : "No hay ejecuciones registradas"} detail={search ? "Prueba con otro término de búsqueda." : "Ejecuta una reconciliación para empezar a registrar resultados."} action={!search ? "Nueva reconciliación" : undefined} onAction={() => navigate("reconcile")} />}
              </>}
            </section>
          )}

          {view === "quality" && (
            <section className="quality-layout">
              <div className="quality-intro"><div className="quality-big-icon"><ShieldCheck size={32} /></div><div><h2>Reglas de integridad</h2><p>El motor compara ambos conjuntos de datos y genera un resultado PASS o FAIL según las comprobaciones.</p></div></div>
              <div className="quality-grid">{Object.entries(checkLabels).map(([key, label], index) => <article className="panel quality-card" key={key}><div className="quality-card-top"><span className="quality-number">0{index + 1}</span><CheckCircle2 size={18} className="quality-check" /></div><h3>{label}</h3><p>{({
                RECORD_COUNTS: "Comprueba si el número total de filas coincide entre origen y destino.",
                MISSING_RECORDS: "Detecta claves que existen en el origen, pero no aparecen en el destino.",
                UNEXPECTED_RECORDS: "Identifica registros presentes en el destino que no existen en el origen.",
                FIELD_DIFFERENCES: "Compara los valores de las columnas compartidas para cada clave coincidente.",
                DUPLICATE_KEYS: "Detecta claves repetidas que impiden identificar un registro de forma inequívoca.",
                BLANK_KEYS: "Cuenta registros que no tienen valor en la columna clave.",
                SCHEMA: "Identifica columnas exclusivas del origen o del destino.",
              })[key]}</p><div className="quality-card-foot"><span>REGLA AUTOMÁTICA</span><span>{key}</span></div></article>)}</div>
              <div className="notice-box quality-note"><Activity size={17} /><p>Las validaciones se ejecutan al enviar archivos desde <strong>Nueva reconciliación</strong>. Esta sección describe las reglas del motor; no representa resultados inventados.</p></div>
            </section>
          )}
          <footer className="page-footer"><span>© MIGRAVALID QA <span className="footer-separator">·</span> Plataforma de calidad de datos</span><span><span className={`pulse-dot ${health === "online" ? "pulse-online" : ""}`} /> API {health === "online" ? "conectada" : health === "checking" ? "verificando" : "desconectada"}</span></footer>
        </div>
      </main>
    </div>
  );
}

function FileDrop({ title, subtitle, file, onFile, onClear, dragging, onDrag }) {
  return (
    <div className={`file-drop ${file ? "file-drop-ready" : ""} ${dragging ? "file-drop-dragging" : ""}`} onDragOver={(event) => { event.preventDefault(); onDrag(true); }} onDragLeave={() => onDrag(false)} onDrop={(event) => { event.preventDefault(); onDrag(false); onFile(event.dataTransfer.files?.[0]); }}>
      <input type="file" accept=".csv,.xlsx" aria-label={title} onChange={(event) => { onFile(event.target.files?.[0]); event.target.value = ""; }} />
      <div className={`drop-icon ${file ? "drop-icon-ready" : ""}`}>{file ? <FileSpreadsheet size={24} /> : <CloudUpload size={24} />}</div>
      <span className="drop-subtitle">{subtitle}</span><strong className="drop-title">{file ? file.name : title}</strong>
      {file ? <><span className="file-size">{(file.size / 1024).toFixed(1)} KB · listo para comparar</span><button type="button" className="remove-file" onClick={(event) => { event.stopPropagation(); onClear(); }}><X size={14} /> Quitar archivo</button></> : <><span className="drop-hint">Arrastra el archivo o <span>explora</span></span><span className="file-formats">CSV / XLSX · máximo 10 MB</span></>}
    </div>
  );
}

function RunTable({ runs, onOpen }) {
  return (
    <div className="table-scroll"><table className="data-table"><thead><tr><th>EJECUCIÓN</th><th>ARCHIVOS</th><th>FILAS</th><th>COMPROBACIONES</th><th>ESTADO</th><th>FECHA</th><th /></tr></thead><tbody>
      {runs.map((run, index) => {
        const summary = getSummary(run);
        const status = getStatus(run);
        return <tr key={String(getRunId(run)) + index} onClick={() => onOpen(run)} className="clickable-row">
          <td><div className="run-id">#{String(getRunId(run)).slice(0, 8)}</div><div className="table-subtext">{summary.key_column ? `Clave: ${summary.key_column}` : "Reconciliación"}</div></td>
          <td><div className="file-cell"><FileSpreadsheet size={15} /><span>{summary.source_file || run.source_file || "Archivo de origen"}</span></div><div className="file-cell file-cell-secondary"><FileSpreadsheet size={15} /><span>{summary.target_file || run.target_file || "Archivo de destino"}</span></div></td>
          <td><strong className="row-count">{number(summary.source_rows)}</strong><div className="table-subtext">origen / {number(summary.target_rows)} destino</div></td>
          <td><strong>{summary.checks_passed ?? "—"} <span className="passed-text">OK</span></strong><div className="table-subtext">{summary.checks_failed ?? "—"} con fallos</div></td>
          <td><StatusPill status={status} /></td><td className="date-cell">{prettyDate(getRunDate(run))}</td><td><button className="row-open" aria-label="Ver ejecución" onClick={(event) => { event.stopPropagation(); onOpen(run); }}><ChevronRight size={17} /></button></td>
        </tr>;
      })}
    </tbody></table></div>
  );
}

function ResultDetails({ result }) {
  const summary = getSummary(result);
  const checks = Array.isArray(result.checks) ? result.checks : result.result?.checks || [];
  return <>
    <div className="result-metrics">
      <div><span>Filas en origen</span><strong>{number(summary.source_rows)}</strong></div>
      <div><span>Filas en destino</span><strong>{number(summary.target_rows)}</strong></div>
      <div><span>Claves coincidentes</span><strong>{number(summary.matched_keys)}</strong></div>
      <div><span>Registros faltantes</span><strong>{number(summary.missing_records)}</strong></div>
      <div><span>Diferencias de campos</span><strong>{number(summary.field_differences)}</strong></div>
    </div>
    <div className="checks-list">{checks.map((check) => <div className="check-result-row" key={check.name}><span className={`check-result-icon ${check.passed ? "check-result-pass" : "check-result-fail"}`}>{check.passed ? <Check size={15} /> : <X size={15} />}</span><div className="check-result-copy"><strong>{checkLabels[check.name] || check.name}</strong><span>{check.passed ? "Comprobación superada" : "Se encontraron diferencias"}</span></div><span className={`check-result-state ${check.passed ? "passed-text" : "failed-text"}`}>{check.passed ? "PASS" : "FAIL"}</span></div>)}</div>
    {checks.filter((check) => !check.passed).map((check) => {
      const detailItems = check.items || check.keys || [];
      return <div className="difference-block" key={`${check.name}-details`}><h4>{checkLabels[check.name] || check.name}: detalles</h4>
        {check.name === "FIELD_DIFFERENCES" && detailItems.length > 0 ? <div className="table-scroll"><table className="data-table compact-table"><thead><tr><th>CLAVE</th><th>COLUMNA</th><th>VALOR ORIGEN</th><th>VALOR DESTINO</th></tr></thead><tbody>{detailItems.slice(0, 100).map((item, index) => <tr key={index}><td>{item.key}</td><td>{item.column}</td><td className="diff-value">{String(item.source_value ?? "∅")}</td><td className="diff-value">{String(item.target_value ?? "∅")}</td></tr>)}</tbody></table></div> : detailItems.length > 0 ? <p className="difference-values">{detailItems.slice(0, 30).map((item) => typeof item === "object" ? JSON.stringify(item) : String(item)).join(", ")}{detailItems.length > 30 ? ` y ${detailItems.length - 30} más...` : ""}</p> : <p className="difference-values">Origen: {check.source_count ?? check.source ?? "—"} · Destino: {check.target_count ?? check.target ?? "—"}</p>}
      </div>;
    })}
    {result.column_comparison && <div className="schema-summary"><h4>Comparación de esquema</h4><p>Columnas compartidas: {result.column_comparison.common_columns?.join(", ") || "Ninguna"}</p><p>Solo origen: {result.column_comparison.source_only_columns?.join(", ") || "Ninguna"}</p><p>Solo destino: {result.column_comparison.target_only_columns?.join(", ") || "Ninguna"}</p></div>}
  </>;
}

function RunDetail({ run, onBack }) {
  const [fullRun, setFullRun] = useState(run);
  useEffect(() => { setFullRun(run); }, [run]);
  const status = getStatus(fullRun);
  const summary = getSummary(fullRun);
  const result = fullRun.result || fullRun;
  return <div className="run-detail">
    <button className="back-button" onClick={onBack}><ChevronLeft size={17} /> Volver al historial</button>
    <div className="panel-heading detail-heading"><div><div className="eyebrow"><span className="eyebrow-line" />DETALLE DE EJECUCIÓN</div><h3>Reconciliación #{String(getRunId(fullRun)).slice(0, 12)}</h3><p>{prettyDate(getRunDate(fullRun))}</p></div><StatusPill status={status} /></div>
    <div className="detail-file-pair"><div className="detail-file"><FileSpreadsheet size={19} /><div><span>ORIGEN</span><strong>{summary.source_file || fullRun.source_file || "Archivo de origen"}</strong></div></div><ArrowLeftRight size={20} className="muted-icon" /><div className="detail-file"><FileSpreadsheet size={19} /><div><span>DESTINO</span><strong>{summary.target_file || fullRun.target_file || "Archivo de destino"}</strong></div></div></div>
    {summary.key_column && <div className="detail-key"><Database size={16} /> Columna clave: <strong>{summary.key_column}</strong></div>}
    {result.checks ? <ResultDetails result={result} /> : <div className="notice-box"><CircleAlert size={17} /><p>El registro fue consultado, pero la API no devolvió el detalle de comprobaciones con el formato esperado. Revisa la estructura del registro en el backend.</p></div>}
  </div>;
}

export default App;
