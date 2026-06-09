:root{--bg:#f8fafc;--sidebar:#ffffff;--prim:#4361ee;--txt:#0F172A;--brd:#e2e8f0;--ok:#10b981;--err:#ef4444;--muted:#64748b;--shadow:0 4px 12px rgba(0,0,0,0.05)}
[data-theme="dark"]{--bg:#0b1120 !important;--sidebar:#111827 !important;--prim:#6366f1 !important;--txt:#f8fafc !important;--brd:#1f2937 !important;--ok:#34d399 !important;--err:#f87171 !important;--muted:#9ca3af !important;--shadow:0 4px 12px rgba(0,0,0,0.3) !important}
[data-theme="light"]{--bg:#f8fafc !important;--sidebar:#ffffff !important;--prim:#4361ee !important;--txt:#0F172A !important;--brd:#e2e8f0 !important;--ok:#10b981 !important;--err:#ef4444 !important;--muted:#64748b !important;--shadow:0 4px 12px rgba(0,0,0,0.05) !important}
*{box-sizing:border-box;transition:background-color .25s ease,color .25s ease,border-color .25s ease,box-shadow .25s ease}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--txt);margin:0;display:flex;height:100vh;overflow:hidden;font-size:14px}
.sidebar{width:280px;min-width:280px;background:var(--sidebar);border-right:1px solid var(--brd);display:flex;flex-direction:column;height:100vh;flex-shrink:0}
.sidebar-body{flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden;padding:16px 16px 8px}
#z-list{flex:1;min-height:0;overflow-y:auto;padding-right:4px;margin-top:8px}
#z-list::-webkit-scrollbar{width:6px}#z-list::-webkit-scrollbar-thumb{background:var(--brd);border-radius:4px}
.app-title{font-size:16px;font-weight:800;color:var(--prim);padding:6px 0 12px;border-bottom:1px solid var(--brd);display:flex;align-items:center;gap:8px}
.app-title svg{width:20px;height:20px;fill:currentColor}
.zones-group-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);padding:12px 10px 4px;white-space:nowrap}
#search{flex-shrink:0;padding:10px 12px;border-radius:8px;border:1px solid var(--brd);background:var(--bg);color:var(--txt);outline:none;width:100%;font-size:13px}
.zone-item{padding:8px 10px;border-radius:8px;cursor:pointer;font-size:13px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center}
.zone-item:hover{background:rgba(67,97,238,0.08)}
.zone-item.active{background:var(--prim);color:#fff}
.zone-count{background:rgba(100,116,139,0.15);color:var(--muted);font-size:11px;padding:2px 8px;border-radius:12px;margin-left:auto;font-weight:600;white-space:nowrap;transition:all .2s}
.zone-item.active .zone-count{background:rgba(255,255,255,0.25);color:#fff}
[data-theme="dark"] .zone-item.active .zone-count{background:rgba(0,0,0,0.25)}
.zone-actions{display:flex;gap:6px;margin-left:8px}
.zone-btn{cursor:pointer;opacity:0.6;transition:0.2s;display:flex;align-items:center}
.zone-btn:hover{opacity:1;transform:scale(1.1)}
.main{flex:1;display:flex;flex-direction:column;min-width:0;min-height:0;overflow:hidden;padding:20px}
#monitor-main{display:flex;flex-direction:column;flex:1;min-height:0;min-width:0}
.filter-bar{flex-shrink:0;padding:12px;border:1px solid var(--brd);border-radius:12px;background:var(--sidebar);margin-bottom:16px;display:flex;gap:10px;align-items:center;box-shadow:var(--shadow)}
.filter-select{padding:8px 10px;border-radius:8px;border:1px solid var(--brd);background:var(--bg);color:var(--txt);font-size:13px;min-width:130px}
.action-group{margin-left:auto;display:flex;gap:8px;align-items:center}
.btn{padding:8px 14px;border-radius:8px;border:1px solid var(--brd);background:var(--sidebar);color:var(--txt);cursor:pointer;font-size:13px;font-weight:500;display:inline-flex;align-items:center;gap:6px;white-space:nowrap;position:relative}
.btn:hover{background:var(--bg);border-color:var(--prim);transform:translateY(-1px);box-shadow:0 2px 6px rgba(0,0,0,0.08)}
.btn-primary{background:var(--prim);color:#fff;border-color:var(--prim)}
.btn-primary:hover{background:color-mix(in srgb,var(--prim) 85%,black)}
.btn-loading{opacity:0.6;pointer-events:none}
.btn-loading::after{content:'';position:absolute;top:50%;left:50%;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;transform:translate(-50%,-50%)}
@keyframes spin{to{transform:translate(-50%,-50%) rotate(360deg)}}
.table-wrap{flex:1;min-height:0;overflow:auto;background:var(--sidebar);border-radius:12px;border:1px solid var(--brd);box-shadow:var(--shadow)}
.table-refresh{animation:tableFade .4s ease}
@keyframes tableFade{from{opacity:0.7}to{opacity:1}}
table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed}
th{padding:10px 6px;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);border-bottom:1px solid var(--brd);cursor:pointer;position:sticky;top:0;z-index:20;box-shadow:0 2px 8px rgba(0,0,0,0.05);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle;background:var(--sidebar)}
th .icon{width:14px;height:14px;fill:currentColor;vertical-align:middle;margin-right:3px}
th:nth-child(1){width:25%;min-width:140px}
th:nth-child(2){width:60px;text-align:center}
th:nth-child(3){width:90px;text-align:center}
th:nth-child(4){width:160px}
th:nth-child(5){width:20%;min-width:130px;text-align:center}
th:nth-child(6){width:65px;text-align:center}
td{padding:10px 6px;border-bottom:1px solid var(--brd);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;transition:all .2s ease}
td:nth-child(1){white-space:normal;word-break:break-word}
td:nth-child(2){text-align:center}
td:nth-child(3){text-align:center}
td:nth-child(4){white-space:normal;overflow:visible;line-height:1.5}
td:nth-child(5){text-align:center}
td:last-child{width:65px;text-align:right}
tr{min-height:54px}
tr:hover td{background:rgba(67,97,238,0.04)}
tr.row-exit td{opacity:0 !important;padding-top:0 !important;padding-bottom:0 !important;height:0 !important;overflow:hidden !important;border-bottom:none !important;transition:all .3s ease !important}
.type-badge{padding:3px 6px;border-radius:4px;color:#fff;font-size:10px;font-weight:600;background:var(--muted);display:inline-block;text-align:center}
.type-badge.A{background:var(--prim)}.type-badge.AAAA{background:#0ea5e9}.type-badge.CNAME{background:#f59e0b;color:#000}.type-badge.MX{background:#8b5cf6}.type-badge.TXT{background:#64748b}.type-badge.PTR{background:var(--ok)}.type-badge.SRV{background:#ec4899}
.src-tag{font-size:10px;font-weight:600;padding:2px 6px;border-radius:4px;background:rgba(0,0,0,0.05);color:var(--muted);display:inline-block}
.actions-cell{display:flex;gap:4px;justify-content:flex-end;align-items:center;height:100%}
.del-btn,.fix-btn,.edit-btn{cursor:pointer;display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:6px;transition:all .15s}
.del-btn:hover{background:rgba(239,68,68,0.1);color:var(--err)}
.fix-btn:hover{background:rgba(67,97,238,0.1);color:var(--prim)}
.edit-btn:hover{background:rgba(245,158,11,0.1);color:#f59e0b}
.status-bar{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;margin-top:12px;background:var(--sidebar);border:1px solid var(--brd);border-radius:8px;font-size:12px;color:var(--muted);flex-shrink:0;box-shadow:0 1px 3px rgba(0,0,0,0.05)}
.sb-section{display:flex;align-items:center;gap:8px}
.sb-divider{width:2px;height:18px;background:var(--brd);margin:0 12px;border-radius:1px;opacity:0.6}
.sb-item{display:flex;align-items:center;gap:6px}
.sb-label{font-weight:700;color:var(--txt)}
.sb-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.sb-dot.ok{background:var(--ok);box-shadow:0 0 4px var(--ok)}
.sb-dot.err{background:var(--err);box-shadow:0 0 4px var(--err)}
.auto-badge{position:relative;overflow:hidden;display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:6px;background:rgba(16,185,129,0.1);color:var(--ok);font-weight:500;font-size:11px;cursor:default}
.auto-badge .dot{width:5px;height:5px;border-radius:50%;background:currentColor;animation:pulse 2s infinite}
.auto-progress{position:absolute;bottom:0;left:0;height:2px;background:var(--ok);width:100%;transform-origin:left;opacity:0.5;animation:countdown var(--ri,30s) linear infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
@keyframes countdown{from{transform:scaleX(1)}to{transform:scaleX(0)}}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);backdrop-filter:blur(4px);align-items:center;justify-content:center;z-index:1000}
.modal-box{background:var(--sidebar);padding:24px;border-radius:14px;width:460px;max-height:90vh;overflow-y:auto;box-shadow:0 12px 24px rgba(0,0,0,0.15);animation:modalIn .25s ease}
@keyframes modalIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
input,select,textarea{width:100%;padding:10px;margin:8px 0;border:1px solid var(--brd);border-radius:8px;background:var(--bg);color:var(--txt);font-family:inherit;font-size:13px}
textarea{resize:vertical;min-height:80px}
#m-type-hint{font-size:11px;color:var(--muted);margin-top:-4px;margin-bottom:8px;font-style:italic;min-height:16px}
.issue-tag{background:rgba(239,68,68,0.1);color:var(--err);padding:2px 4px;border-radius:3px;font-size:9px;font-weight:500;margin-left:4px;vertical-align:middle}
.mac-addr{color:var(--prim);font-size:10px;font-family:ui-monospace,SFMono-Regular,monospace;margin-top:2px;opacity:0.8}
.lease-bar{height:4px;background:var(--brd);border-radius:2px;margin:3px 0;overflow:hidden}
.lease-bar-fill{height:100%;border-radius:2px;background:var(--ok);transition:width .4s ease}
.lease-bar-fill.warning{background:#f59e0b}.lease-bar-fill.critical{background:var(--err)}
.toast-container{position:fixed;top:20px;right:20px;z-index:1100;display:flex;flex-direction:column;gap:8px;pointer-events:none}
.toast{background:var(--sidebar);border:1px solid var(--brd);border-radius:10px;padding:12px 16px;font-size:13px;animation:toastIn .25s ease;box-shadow:0 8px 16px rgba(0,0,0,0.12);pointer-events:auto;white-space:pre-wrap;display:flex;align-items:center;justify-content:space-between;gap:12px;backdrop-filter:blur(8px)}
.toast.success{border-left:4px solid var(--ok)}.toast.error{border-left:4px solid var(--err)}
.toast-copy{cursor:pointer;opacity:0.6;font-size:14px;flex-shrink:0}
.toast-copy:hover{opacity:1}
@keyframes toastIn{from{transform:translateX(24px);opacity:0}to{transform:translateX(0);opacity:1}}
#audit-content{font-family:ui-monospace,SFMono-Regular,monospace;font-size:12px;white-space:pre-wrap;color:var(--txt);max-height:60vh;overflow-y:auto;background:var(--bg);padding:12px;border-radius:8px;border:1px solid var(--brd)}
.auth-only{display:none !important}
body.is-auth .auth-only{display:inline-flex !important}
.settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.settings-group{margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--brd)}
.settings-group:last-child{border-bottom:none}
.settings-label{font-size:12px;color:var(--muted);margin-bottom:4px;display:block;font-weight:500}
.restart-warn{background:rgba(245,158,11,0.1);color:#f59e0b;padding:10px;border-radius:8px;font-size:12px;margin-top:12px;display:none;border:1px solid rgba(245,158,11,0.2)}
.icon{width:16px;height:16px;flex-shrink:0;fill:currentColor}
#search-clear:hover{color:var(--err)}
