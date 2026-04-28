export function resolveDisplayName(user) {
  const fullName = String(user?.full_name || "").trim();
  if (fullName) {
    const firstName = fullName.split(/\s+/).find(Boolean);
    if (firstName) return firstName;
  }
  const email = String(user?.email || "").trim();
  if (email && email.includes("@")) return email.split("@")[0];
  return "";
}

export function resolveDayPeriodGreeting(date = new Date()) {
  const hour = Number(date?.getHours?.());
  if (Number.isNaN(hour)) return "Olá";
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

export function resolvePersonalGreeting(user, date = new Date()) {
  const name = resolveDisplayName(user);
  if (!name) return "";
  return `${resolveDayPeriodGreeting(date)}, ${name}. `;
}
