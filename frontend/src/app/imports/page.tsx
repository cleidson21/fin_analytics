import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

export default function ImportsRedirectPage() {
  redirect("/governance/import");
}