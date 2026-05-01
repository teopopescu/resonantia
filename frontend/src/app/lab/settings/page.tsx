"use client";

import { useState } from "react";
import {
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
import {
  ElabFTWLogo,
  BenchlingLogo,
  DotmaticsLogo,
} from "@/components/icons/integration-logos";
import { PageHeader } from "@/components/lab/primitives/page-header";
import { Chip } from "@/components/lab/primitives/data-table";
import { cn } from "@/lib/utils";

type ConnectionStatus = "connected" | "error" | "unconfigured";

const STATUS_TONE: Record<ConnectionStatus, "brand" | "mch" | "default"> = {
  connected: "brand",
  error: "mch",
  unconfigured: "default",
};

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  connected: "connected",
  error: "error",
  unconfigured: "not configured",
};

const STATUS_ICON: Record<ConnectionStatus, React.ReactNode> = {
  connected: <CheckCircle2 size={11} />,
  error: <XCircle size={11} />,
  unconfigured: <AlertCircle size={11} />,
};

const inputBase =
  "w-full px-3 py-2 rounded-[3px] border border-line bg-bg text-[13px] text-ink focus:outline-none focus:border-brand/40 transition-colors placeholder:text-ink-subtle";

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block font-mono text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-subtle mb-1.5">
      {children}
    </label>
  );
}

function IntegrationCard({
  marker,
  name,
  description,
  logo,
  status,
  comingSoon,
  children,
}: {
  marker: string;
  name: string;
  description: string;
  logo: React.ReactNode;
  status?: ConnectionStatus;
  comingSoon?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-[5px] border bg-surface overflow-hidden",
        comingSoon ? "border-line opacity-70" : "border-line"
      )}
    >
      <div className="flex items-center justify-between px-5 py-4 border-b border-line bg-bg">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] tracking-[0.04em] uppercase text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
            {marker}
          </span>
          <div className="w-9 h-9 rounded-[3px] bg-surface border border-line flex items-center justify-center">
            {logo}
          </div>
          <div>
            <h3 className="text-[14px] font-semibold tracking-[-0.01em] text-ink">
              {name}
            </h3>
            <p className="font-mono text-[11px] tracking-[0.02em] text-ink-muted mt-0.5">
              {description}
            </p>
          </div>
        </div>
        {comingSoon ? (
          <Chip tone="default">
            <Clock size={11} />
            coming soon
          </Chip>
        ) : status ? (
          <Chip tone={STATUS_TONE[status]}>
            {STATUS_ICON[status]}
            {STATUS_LABEL[status]}
          </Chip>
        ) : null}
      </div>
      {children}
    </div>
  );
}

export default function SettingsPage() {
  const [elabUrl, setElabUrl] = useState("");
  const [elabApiKey, setElabApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(
    "unconfigured"
  );
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
      setTestMessage(result.message || "Connection successful.");
    } catch {
      setConnectionStatus("error");
      setTestMessage(
        "Connection failed. Check your URL and API key, or ensure the backend is running."
      );
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
      setTestMessage("Configuration saved.");
    } catch {
      setTestMessage("Failed to save remotely. Stored locally as fallback.");
      localStorage.setItem(
        "resonantia-elabftw-config",
        JSON.stringify({ url: elabUrl, api_key: "***" })
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col h-full bg-bg">
      <PageHeader
        marker="09"
        markerLabel="Settings · integrations"
        title="Settings"
        meta={
          <>
            integrations · workspace · billing ·{" "}
            <em className="not-italic text-brand">eLabFTW available</em>
          </>
        }
      />

      <div className="flex-1 overflow-auto px-6 py-8 min-h-0">
        <div className="max-w-3xl mx-auto space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-4 font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle">
              <Link2 size={13} className="text-brand" />
              <span className="text-brand">›</span> integrations
            </div>

            {/* eLabFTW */}
            <IntegrationCard
              marker="INT/01"
              name="eLabFTW"
              description="Electronic lab notebook · sync entries"
              logo={<ElabFTWLogo size={24} />}
              status={connectionStatus}
            >
              <div className="p-5 space-y-4">
                <div>
                  <FieldLabel>server url</FieldLabel>
                  <input
                    type="url"
                    value={elabUrl}
                    onChange={(e) => setElabUrl(e.target.value)}
                    placeholder="https://elabftw.example.com"
                    className={cn(inputBase, "font-mono")}
                  />
                </div>

                <div>
                  <FieldLabel>api key</FieldLabel>
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={elabApiKey}
                      onChange={(e) => setElabApiKey(e.target.value)}
                      placeholder="enter your eLabFTW API key"
                      className={cn(inputBase, "font-mono pr-10")}
                    />
                    <button
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-subtle hover:text-ink transition-colors"
                      type="button"
                    >
                      {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                </div>

                {testMessage && (
                  <div
                    className={cn(
                      "flex items-start gap-2 px-3 py-2 rounded-[3px] font-mono text-[11.5px] tracking-[0.02em] border",
                      connectionStatus === "connected"
                        ? "bg-brand-soft border-brand/30 text-brand"
                        : connectionStatus === "error"
                        ? "bg-mch-soft border-mch/30 text-mch"
                        : "bg-bg border-line text-ink-muted"
                    )}
                  >
                    {connectionStatus === "connected" ? (
                      <CheckCircle2 size={13} className="shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle size={13} className="shrink-0 mt-0.5" />
                    )}
                    {testMessage}
                  </div>
                )}

                <div className="flex items-center gap-2 pt-2 border-t border-line">
                  <button
                    onClick={handleTestConnection}
                    disabled={testing}
                    className="inline-flex items-center gap-2 px-3 py-2 text-[13px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-bg transition-colors disabled:opacity-60"
                  >
                    {testing ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Link2 size={13} />
                    )}
                    Test connection
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] hover:bg-brand-strong transition-colors disabled:opacity-60"
                    style={{
                      boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)",
                    }}
                  >
                    {saving && <Loader2 size={13} className="animate-spin" />}
                    Save
                  </button>
                </div>
              </div>
            </IntegrationCard>

            {/* Benchling */}
            <div className="mt-4">
              <IntegrationCard
                marker="INT/02"
                name="Benchling"
                description="Notebook · registry · plates · roadmapped"
                logo={<BenchlingLogo size={24} />}
                comingSoon
              >
                <div className="p-5 space-y-4">
                  <div>
                    <FieldLabel>tenant url</FieldLabel>
                    <input
                      type="url"
                      disabled
                      placeholder="https://yourorg.benchling.com"
                      className={cn(inputBase, "font-mono opacity-60 cursor-not-allowed")}
                    />
                  </div>
                  <div>
                    <FieldLabel>api key</FieldLabel>
                    <input
                      type="password"
                      disabled
                      placeholder="enter your Benchling API key"
                      className={cn(inputBase, "font-mono opacity-60 cursor-not-allowed")}
                    />
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-line">
                    <button
                      disabled
                      className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] opacity-40 cursor-not-allowed"
                    >
                      Connect
                    </button>
                    <button className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.04em] text-brand hover:text-brand-strong transition-colors">
                      <Bell size={11} />
                      notify me
                    </button>
                  </div>
                </div>
              </IntegrationCard>
            </div>

            {/* Dotmatics */}
            <div className="mt-4">
              <IntegrationCard
                marker="INT/03"
                name="Dotmatics"
                description="Browser · studies · compound registration"
                logo={<DotmaticsLogo size={24} />}
                comingSoon
              >
                <div className="p-5 space-y-4">
                  <div>
                    <FieldLabel>server url</FieldLabel>
                    <input
                      type="url"
                      disabled
                      placeholder="https://yourorg.dotmatics.net"
                      className={cn(inputBase, "font-mono opacity-60 cursor-not-allowed")}
                    />
                  </div>
                  <div>
                    <FieldLabel>api key</FieldLabel>
                    <input
                      type="password"
                      disabled
                      placeholder="enter your Dotmatics API key"
                      className={cn(inputBase, "font-mono opacity-60 cursor-not-allowed")}
                    />
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-line">
                    <button
                      disabled
                      className="inline-flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium bg-brand text-white rounded-[3px] opacity-40 cursor-not-allowed"
                    >
                      Connect
                    </button>
                    <button className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.04em] text-brand hover:text-brand-strong transition-colors">
                      <Bell size={11} />
                      notify me
                    </button>
                  </div>
                </div>
              </IntegrationCard>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
