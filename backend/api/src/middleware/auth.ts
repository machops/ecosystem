import { type Request, type Response, type NextFunction, type RequestHandler } from "express";
import { createClient } from "@supabase/supabase-js";

// ── Types ───────────────────────────────────────────────────────────

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: string;
    urn: string;
  };
}

// ── Supabase Client ─────────────────────────────────────────────────

const supabase = createClient(
  process.env.SUPABASE_URL || "",
  process.env.SUPABASE_SERVICE_ROLE_KEY || ""
);

// ── requireAuth — validates Bearer token via Supabase ───────────────

export const requireAuth: RequestHandler = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) {
    res.status(401).json({ error: "No token" });
    return;
  }

  const { data, error } = await supabase.auth.getUser(token);
  if (error || !data.user) {
    res.status(401).json({ error: "Invalid token" });
    return;
  }

  (req as AuthenticatedRequest).user = {
    id: data.user.id,
    email: data.user.email || "",
    role: data.user.role || "member",
    urn: `urn:indestructibleeco:user:${data.user.id}`,
  };
  next();
};

// ── adminOnly — restricts to admin role ─────────────────────────────

export const adminOnly: RequestHandler = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  const authReq = req as AuthenticatedRequest;
  if (!authReq.user) {
    res.status(401).json({ error: "Authentication required" });
    return;
  }

  if (authReq.user.role !== "admin" && authReq.user.role !== "service_role") {
    res.status(403).json({ error: "Admin access required" });
    return;
  }

  next();
};