import {
	AUTO_MODE,
	DARK_MODE,
	DEFAULT_THEME,
	LIGHT_MODE,
} from "@constants/constants.ts";
import { expressiveCodeConfig, siteConfig } from "@/config";
import type { LIGHT_DARK_MODE } from "@/types/config";

export function getDefaultHue(): number {
	return siteConfig.themeColor.hue;
}

export function getHue(): number {
	try {
		const stored =
			typeof window !== "undefined" ? window.localStorage.getItem("hue") : null;
		const hue = stored === null ? NaN : Number(stored);
		return Number.isFinite(hue) && hue >= 0 && hue <= 360
			? hue
			: getDefaultHue();
	} catch {
		return getDefaultHue();
	}
}

export function setHue(hue: number): void {
	if (typeof document === "undefined") return;
	try {
		window.localStorage.setItem("hue", String(hue));
	} catch {}
	const r = document.querySelector(":root") as HTMLElement;
	if (!r) {
		return;
	}
	r.style.setProperty("--hue", String(hue));
}

export function applyThemeToDocument(theme: LIGHT_DARK_MODE) {
	if (typeof document === "undefined") return;
	switch (theme) {
		case LIGHT_MODE:
			document.documentElement.classList.remove("dark");
			break;
		case DARK_MODE:
			document.documentElement.classList.add("dark");
			break;
		case AUTO_MODE:
			if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
				document.documentElement.classList.add("dark");
			} else {
				document.documentElement.classList.remove("dark");
			}
			break;
	}

	// Set the theme for Expressive Code
	document.documentElement.setAttribute(
		"data-theme",
		expressiveCodeConfig.theme,
	);
}

export function setTheme(theme: LIGHT_DARK_MODE): void {
	try {
		window.localStorage.setItem("theme", theme);
	} catch {}
	applyThemeToDocument(theme);
}

export function getStoredTheme(): LIGHT_DARK_MODE {
	try {
		const stored = window.localStorage.getItem("theme") as LIGHT_DARK_MODE;
		return [LIGHT_MODE, DARK_MODE, AUTO_MODE].includes(stored)
			? stored
			: DEFAULT_THEME;
	} catch {
		return DEFAULT_THEME;
	}
}
