export function cn(...values: Array<string | false | null | undefined>) { return values.filter(Boolean).join(" "); }
export const humanize = (value: string) => value.replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
