import { auth } from "@clerk/nextjs/server";

export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { email } = await request.json();

  if (!email || typeof email !== "string" || !email.includes("@")) {
    return Response.json(
      { error: "A valid email address is required" },
      { status: 400 }
    );
  }

  const response = await fetch("https://api.clerk.com/v1/invitations", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.CLERK_SECRET_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email_address: email,
      redirect_url: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/lab`,
      notify: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    return Response.json(
      {
        error:
          error.errors?.[0]?.message || "Failed to send invitation",
      },
      { status: response.status }
    );
  }

  const invitation = await response.json();
  return Response.json({ success: true, invitation });
}
