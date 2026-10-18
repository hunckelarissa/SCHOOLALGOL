package org.myau.shaya.ide.toolchain;

import java.io.File;

/**
 * Resolves docs and examples paths under the installed toolchain / repo.
 */
public final class ShayaDocs {

	private ShayaDocs() {
	}

	/**
	 * Grammar / extension map doc. Prefer {@code docs/GRAMMAR.md} (synced by
	 * install_dropins); fall back to repo-relative paths from toolchain home.
	 */
	public static File findExtensionMap() {
		return firstExisting(
				rel("docs/GRAMMAR.md"),
				rel("../docs/GRAMMAR.md"),
				rel("../../docs/GRAMMAR.md"),
				rel("GRAMMAR.md"),
				rel("../GRAMMAR.md"),
				rel("../../GRAMMAR.md"),
				rel("docs/EXTENSION_MAP.md"),
				rel("../docs/EXTENSION_MAP.md"),
				rel("../../docs/EXTENSION_MAP.md"));
	}

	public static File findTrackReadme() {
		return firstExisting(
				rel("examples/track/README.md"),
				rel("../examples/track/README.md"),
				rel("../../examples/track/README.md"));
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
