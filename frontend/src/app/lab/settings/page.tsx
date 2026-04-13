"use client";

import { useState } from "react";
import {
  Settings,
  Link2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Eye,
  EyeOff,
  Clock,
  Bell,
} from "lucide-react";
import { api } from "@/lib/api";
import { ElabFTWLogo, BenchlingLogo, DotmaticsLogo } from "@/components/icons/integration-logos";

type ConnectionStatus = "connected" | "error" | "unconfigured";

const STATUS_CONFIG: Record<
  ConnectionStatus,
  { label: string; icon: React.ReactNode; color: string; bg: string }
> = {
  connected: {
    label: "Connected",
    icon: <CheckCircle2 size={14} />,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  error: {
    label: "Error",
    icon: <XCircle size={14} />,
    color: "text-red-600",
    bg: "bg-red-50",
  },
  unconfigured: {
    label: "Not configured",
    icon: <AlertCircle size={14} />,
    color: "text-gray-500",
    bg: "bg-gray-100",
  },
};

export default function SettingsPage() {
  const [elabUrl, setElabUrl] = useState("");
  const [elabApiKey, setElabApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("unconfigured");
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testMessage, setTestMessage] = useState("");

  async function handleTestConnection() {
    if (!elabUrl.trim() || !elabApiKey.trim()) {
      setTestMessage("URL and API key are required.");
      setConnectionStatus("error");
      return;
    }
    setTesting(true);
    setTestMessage("");
    try {
      const result = await api<{ status: string; message?: string }>(
        "/api/v1/integrations/elabftw/test",
        {
          method: "POST",
          body: JSON.stringify({ url: elabUrl, api_key: elabApiKey }),
        }
      );
      setConnectionStatus("connected");
      setTestMessage(result.message || "Connection successful!");
    } catch {
      setConnectionStatus("error");
      setTestMessage("Connection failed. Check your URL and API key, or ensure the backend is running.");
    } finally {
      setTesting(false);
    }
  }

  async function handleSave() {
    if (!elabUrl.trim() || !elabApiKey.trim()) {
      setTestMessage("URL and API key are required.");
      return;
    }
    setSaving(true);
    setTestMessage("");
    try {
      await api("/api/v1/integrations/config", {
        method: "POST",
        body: JSON.stringify({
          integration: "elabftw",
          config: { url: elabUrl, api_key: elabApiKey },
        }),
      });
      setTestMessage("Configuration saved successfully.");
    } catch {
      setTestMessage("Failed to save configuration. Settings stored locally.");
      // Save to localStorage as fallback
      localStorage.setItem(
        "resonantia-elabftw-config",
        JSON.stringify({ url: elabUrl, api_key: "***" })
      );
    } finally {
      setSaving(false);
    }
  }

  const statusCfg = STATUS_CONFIG[connectionStatus];
  const inputClass =
    "w-full px-3 py-2 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/40";

  return (
    <div className="flex flex-col h-full bg-cream">
      {/* Header */}
      <div className="px-6 py-4 bg-surface border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-amber/15 flex items-center justify-center">
            <Settings size={18} className="text-amber" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-charcoal">Settings</h1>
            <p className="text-xs text-muted">Configure integrations and preferences</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Integrations section */}
          <div>
            <h2 className="text-sm font-semibold text-charcoal mb-4 flex items-center gap-2">
              <Link2 size={16} className="text-amber" />
              Integrations
            </h2>

            {/* eLabFTW card */}
            <div className="rounded-2xl border border-border bg-surface overflow-hidden mb-4">
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                    <ElabFTWLogo size={28} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-charcoal">eLabFTW</h3>
                    <p className="text-xs text-muted">Electronic lab notebook integration</p>
                  </div>
                </div>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusCfg.bg} ${statusCfg.color}`}
                >
                  {statusCfg.icon}
                  {statusCfg.label}
                </span>
              </div>

              <div className="p-5 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-charcoal mb-1">Server URL</label>
                  <input
                    type="url"
                    value={elabUrl}
                    onChange={(e) => setElabUrl(e.target.value)}
                    placeholder="https://elabftw.example.com"
                    className={inputClass}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-charcoal mb-1">API Key</label>
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={elabApiKey}
                      onChange={(e) => setElabApiKey(e.target.value)}
                      placeholder="Enter your eLabFTW API key"
                      className={`${inputClass} pr-10`}
                    />
                    <button
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-charcoal transition-colors"
                    >
                      {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                </div>

                {testMessage && (
                  <div
                    className={`flex items-start gap-2 px-3 py-2 rounded-lg text-xs ${
                      connectionStatus === "connected"
                        ? "bg-emerald-50 text-emerald-700"
                        : connectionStatus === "error"
                        ? "bg-red-50 text-red-700"
                        : "bg-gray-50 text-gray-700"
                    }`}
                  >
                    {connectionStatus === "connected" ? (
                      <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle size={14} className="shrink-0 mt-0.5" />
                    )}
                    {testMessage}
                  </div>
                )}

                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={handleTestConnection}
                    disabled={testing}
                    className="flex items-center gap-1.5 px-4 py-2 text-sm text-muted hover:text-charcoal rounded-lg border border-border hover:border-muted transition-colors disabled:opacity-60"
                  >
                    {testing ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Link2 size={14} />
                    )}
                    Test Connection
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg hover:bg-amber-light transition-colors disabled:opacity-60"
                  >
                    {saving && <Loader2 size={14} className="animate-spin" />}
                    Save
                  </button>
                </div>
              </div>
            </div>

            {/* Benchling card — Coming Soon */}
            <div className="rounded-2xl border border-border bg-surface overflow-hidden mb-4 opacity-60 relative">
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#4B6EF5]/10 flex items-center justify-center">
                    <BenchlingLogo size={28} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-charcoal">Benchling</h3>
                    <p className="text-xs text-muted">Sync notebook entries, registry entities, and plate data with your Benchling tenant.</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                  <Clock size={12} />
                  Coming Soon
                </span>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-charcoal mb-1">Tenant URL</label>
                  <input
                    type="url"
                    disabled
                    placeholder="https://yourorg.benchling.com"
                    className={`${inputClass} opacity-50 cursor-not-allowed`}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-charcoal mb-1">API Key</label>
                  <input
                    type="password"
                    disabled
                    placeholder="Enter your Benchling API key"
                    className={`${inputClass} opacity-50 cursor-not-allowed`}
                  />
                </div>
                <div className="flex items-center justify-between pt-1">
                  <button
                    disabled
                    className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg opacity-50 cursor-not-allowed"
                  >
                    Connect
                  </button>
                  <button className="flex items-center gap-1.5 text-xs text-amber hover:text-amber-light transition-colors">
                    <Bell size={12} />
                    Notify me
                  </button>
                </div>
              </div>
            </div>

            {/* Dotmatics card — Coming Soon */}
            <div className="rounded-2xl border border-border bg-surface overflow-hidden opacity-60 relative">
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#00897B]/10 flex items-center justify-center">
                    <DotmaticsLogo size={28} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-charcoal">Dotmatics</h3>
                    <p className="text-xs text-muted">Connect to Dotmatics Browser, Studies, and compound registration.</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                  <Clock size={12} />
                  Coming Soon
                </span>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-charcoal mb-1">Server URL</label>
                  <input
                    type="url"
                    disabled
                    placeholder="https://yourorg.dotmatics.net"
                    className={`${inputClass} opacity-50 cursor-not-allowed`}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-charcoal mb-1">API Key</label>
                  <input
                    type="password"
                    disabled
                    placeholder="Enter your Dotmatics API key"
                    className={`${inputClass} opacity-50 cursor-not-allowed`}
                  />
                </div>
                <div className="flex items-center justify-between pt-1">
                  <button
                    disabled
                    className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-amber text-charcoal rounded-lg opacity-50 cursor-not-allowed"
                  >
                    Connect
                  </button>
                  <button className="flex items-center gap-1.5 text-xs text-amber hover:text-amber-light transition-colors">
                    <Bell size={12} />
                    Notify me
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
