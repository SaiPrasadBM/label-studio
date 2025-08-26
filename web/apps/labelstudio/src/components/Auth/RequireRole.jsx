import React from "react";
import { useCurrentUser } from "../../providers/CurrentUser";

export const RequireRole = ({ fineRole = "EDITOR", children, fallback = null }) => {
  const { user, isInProgress } = useCurrentUser();

  if (isInProgress) return null;

  const ok = user?.fine_role === fineRole;

  if (!ok) return fallback;

  return <>{children}</>;
};
