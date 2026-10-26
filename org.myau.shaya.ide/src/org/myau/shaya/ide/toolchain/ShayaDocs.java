package org.myau.shaya.ide.toolchain;

import java.io.File;
import java.util.Locale;

import org.eclipse.core.runtime.Platform;

/**
 * Resolves docs and examples paths under the installed toolchain / repo.
 */
public final class ShayaDocs {

	private ShayaDocs() {
	}

	/** Workbench / OSGi NL language is Russian ({@code ru…}). */
	public static boolean isRussianLocale() {
		String nl = Platform.getNL();
		if (nl == null || nl.isBlank()) {
			return "ru".equals(Locale.getDefault().getLanguage());
		}
		return nl.toLowerCase(Locale.ROOT).startsWith("ru");
	}

	/**
	 * Grammar doc. Prefer {@code GRAMMAR.ru.md} when workbench language is
	 * {@code ru}, else {@code GRAMMAR.md}; fall back to the other if missing.
	 */
	public static File findExtensionMap() {
		boolean ru = isRussianLocale();
		String preferred = ru ? "GRAMMAR.ru.md" : "GRAMMAR.md";
		String fallback = ru ? "GRAMMAR.md" : "GRAMMAR.ru.md";
		File hit = firstExisting(grammarCandidates(preferred));
		if (hit != null) {
			return hit;
		}
		hit = firstExisting(grammarCandidates(fallback));
		if (hit != null) {
			return hit;
		}
		return firstExisting(
				rel("docs/EXTENSION_MAP.md"),
				rel("../docs/EXTENSION_MAP.md"),
				rel("../../docs/EXTENSION_MAP.md"));
	}

	/**
	 * Learning-track README. Prefer {@code README.ru.md} for Russian locale,
	 * else {@code README.md}; fall back to the other if missing.
	 */
	public static File findTrackReadme() {
		boolean ru = isRussianLocale();
		String preferred = ru ? "README.ru.md" : "README.md";
		String fallback = ru ? "README.md" : "README.ru.md";
		File hit = firstExisting(trackReadmeCandidates(preferred));
		if (hit != null) {
			return hit;
		}
		return firstExisting(trackReadmeCandidates(fallback));
	}

	public static File findTrackDir() {
		File readme = findTrackReadme();
		if (readme != null) {
			return readme.getParentFile();
		}
		return firstExisting(
				rel("examples/track"),
				rel("../examples/track"),
				rel("../../examples/track"));
	}

	private static File[] grammarCandidates(String fileName) {
		return new File[] {
				rel("docs/" + fileName),
				rel("../docs/" + fileName),
				rel("../../docs/" + fileName),
				rel(fileName),
				rel("../" + fileName),
				rel("../../" + fileName)
		};
	}

	private static File[] trackReadmeCandidates(String fileName) {
		return new File[] {
				rel("examples/track/" + fileName),
				rel("../examples/track/" + fileName),
				rel("../../examples/track/" + fileName)
		};
	}

	private static File rel(String relative) {
		File home = ShayaToolchain.getToolchainHome();
		if (home == null) {
			return null;
		}
		return new File(home, relative);
	}

	private static File firstExisting(File... candidates) {
		for (File c : candidates) {
			if (c == null) {
				continue;
			}
			try {
				File f = c.getCanonicalFile();
				if (f.exists()) {
					return f;
				}
			} catch (Exception ignored) {
			}
		}
		return null;
	}
}
