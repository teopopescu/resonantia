interface EmailTemplateProps {
  inviteUrl?: string;
  recipientName?: string;
}

export default function EmailTemplate({
  inviteUrl = "https://resonantia.app/lab",
  recipientName,
}: EmailTemplateProps) {
  return (
    <div
      style={{
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        backgroundColor: "#FAF8F5",
        padding: "40px 0",
      }}
    >
      <div
        style={{
          maxWidth: "560px",
          margin: "0 auto",
          backgroundColor: "#FFFFFF",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}
      >
        {/* Header */}
        <div
          style={{
            backgroundColor: "#2D2A26",
            padding: "32px 40px",
            textAlign: "center" as const,
          }}
        >
          <div
            style={{
              display: "inline-block",
              width: "44px",
              height: "44px",
              lineHeight: "44px",
              borderRadius: "10px",
              backgroundColor: "#E8A849",
              color: "#2D2A26",
              fontFamily: '"Playfair Display", Georgia, serif',
              fontWeight: 700,
              fontSize: "22px",
              textAlign: "center" as const,
            }}
          >
            R
          </div>
          <h1
            style={{
              fontFamily: '"Playfair Display", Georgia, serif',
              fontSize: "24px",
              fontWeight: 700,
              color: "#FFFFFF",
              margin: "16px 0 0 0",
              letterSpacing: "-0.01em",
            }}
          >
            Resonantia
          </h1>
        </div>

        {/* Body */}
        <div style={{ padding: "40px" }}>
          <h2
            style={{
              fontFamily: '"Playfair Display", Georgia, serif',
              fontSize: "20px",
              fontWeight: 700,
              color: "#2D2A26",
              margin: "0 0 12px 0",
            }}
          >
            You&apos;ve been invited to Resonantia Lab
          </h2>

          <p
            style={{
              fontSize: "15px",
              lineHeight: "1.6",
              color: "#5C5955",
              margin: "0 0 8px 0",
            }}
          >
            {recipientName ? `Hi ${recipientName},` : "Hi,"}
          </p>

          <p
            style={{
              fontSize: "15px",
              lineHeight: "1.6",
              color: "#5C5955",
              margin: "0 0 20px 0",
            }}
          >
            A colleague has invited you to join{" "}
            <strong style={{ color: "#2D2A26" }}>Resonantia Lab</strong> — the
            agentic OS for lab informatics. Automate plate mapping, analyze
            microscopy images, manage sample inventories, and accelerate your
            research with AI-powered workflows.
          </p>

          {/* CTA Button */}
          <div style={{ textAlign: "center" as const, margin: "32px 0" }}>
            <a
              href={inviteUrl}
              style={{
                display: "inline-block",
                padding: "14px 36px",
                backgroundColor: "#E8A849",
                color: "#2D2A26",
                fontSize: "15px",
                fontWeight: 600,
                textDecoration: "none",
                borderRadius: "10px",
                letterSpacing: "0.01em",
              }}
            >
              Accept Invitation
            </a>
          </div>

          <p
            style={{
              fontSize: "13px",
              lineHeight: "1.6",
              color: "#9A9691",
              margin: "0",
            }}
          >
            If you weren&apos;t expecting this invitation, you can safely ignore
            this email.
          </p>
        </div>

        {/* Divider */}
        <div
          style={{
            height: "1px",
            backgroundColor: "#EEEBE7",
            margin: "0 40px",
          }}
        />

        {/* Footer */}
        <div
          style={{
            padding: "24px 40px",
            textAlign: "center" as const,
          }}
        >
          <p
            style={{
              fontSize: "13px",
              color: "#9A9691",
              margin: "0 0 4px 0",
              fontFamily: '"Playfair Display", Georgia, serif',
              fontStyle: "italic",
            }}
          >
            Resonantia — The New Way Labs Work
          </p>
          <p style={{ fontSize: "12px", color: "#C4C0BC", margin: 0 }}>
            resonantia.app
          </p>
        </div>
      </div>
    </div>
  );
}
