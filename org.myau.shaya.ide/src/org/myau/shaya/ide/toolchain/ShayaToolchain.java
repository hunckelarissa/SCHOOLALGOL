package org.myau.shaya.ide.toolchain;

import java.io.File;
import java.net.URI;
import java.net.URL;
import java.util.Locale;

import org.eclipse.core.runtime.FileLocator;
import org.eclipse.core.runtime.Platform;
import org.eclipse.jface.preference.IPreferenceStore;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.prefs.ShayaPreferenceConstants;
import org.osgi.framework.Bundle;

/**
 * Locates the SCHOOLALGOL ALG toolchain under Eclipse dropins and the run wrapper.
 * Single engine: {@code .alg} → SCHOOLALGOL ({@code main.py}).
 */
public final class ShayaToolchain {

	/** Dropins folder name under eclipse/dropins/. */
	public static final String DROPINS_FOLDER = "schoolalgol-shaya";

	/** Engine id returned by {@link #engineIdFor(File)} — stable, used by wrapper + prefs. */
	public static final String ENGINE_ALG = "schoolalgol";

	/** Interpreter folder under toolchain {@code interpreters/}. */
	public static final String ENGINE_DIR = "SchoolAlgol";

	private ShayaToolchain() {
	}

	public static File getToolchainHome() {
		IPreferenceStore prefs = Activator.getDefault().getPreferenceStore();
		String configured = prefs.getString(ShayaPreferenceConstants.TOOLCHAIN_HOME);
		if (configured != null && !configured.isBlank()) {
			File f = new File(configured.trim());
			if (f.isDirectory()) {
				return f;
			}
		}

		File fromBundle = locateBesideBundle();
		if (fromBundle != null) {
			return fromBundle;
		}

		try {
			URL install = Platform.getInstallLocation().getURL();
			File home = new File(install.toURI());
			File dropin = new File(home, "dropins" + File.separator + DROPINS_FOLDER);
			if (dropin.isDirectory()) {
				return dropin;
			}
			// Legacy name from the multi-engine plugin
			File legacy = new File(home, "dropins" + File.separator + "myau-shaya-plugin");
			if (legacy.isDirectory()) {
				return legacy;
			}
		} catch (Exception ignored) {
		}

		return null;
	}

	private static File locateBesideBundle() {
		try {
			Bundle bundle = Platform.getBundle(Activator.PLUGIN_ID);
			if (bundle == null) {
				return null;
			}
			URL entry = bundle.getEntry("/");
			if (entry == null) {
				return null;
			}
			URL fileUrl = FileLocator.toFileURL(entry);
			File dir = new File(fileUrl.getPath());
			if (!dir.exists()) {
				dir = new File(URI.create(fileUrl.toString()));
			}
			if (dir.isFile()) {
				dir = dir.getParentFile();
			}
			if (dir == null) {
				return null;
			}
			if (looksLikeToolchain(dir)) {
				return dir;
			}
			File parent = dir.getParentFile();
			if (parent != null && looksLikeToolchain(parent)) {
				return parent;
			}
			if (parent != null) {
				File sibling = new File(parent, DROPINS_FOLDER);
				if (looksLikeToolchain(sibling)) {
					return sibling;
				}
				File legacy = new File(parent, "myau-shaya-plugin");
				if (looksLikeToolchain(legacy)) {
					return legacy;
				}
			}
			return dir;
		} catch (Exception e) {
			return null;
		}
	}

	private static boolean looksLikeToolchain(File dir) {
		return new File(dir, "tools").isDirectory() || new File(dir, "interpreters").isDirectory();
	}

	/** tools/shaya-run.bat inside the toolchain home. */
	public static File getRunWrapper() {
		File home = getToolchainHome();
		if (home == null) {
			return null;
		}
		File bat = new File(home, "tools" + File.separator + "shaya-run.bat");
		return bat.isFile() ? bat : null;
	}

	/**
	 * Hard extension map: only {@code .alg} → SCHOOLALGOL.
	 *
	 * @return engine id, or {@code null} if the extension is not ALG
	 */
	public static String engineIdFor(File source) {
		if (source == null) {
			return null;
		}
		return engineIdForName(source.getName());
	}

	public static String engineIdForName(String fileName) {
		if (fileName == null) {
			return null;
		}
		String name = fileName.toLowerCase(Locale.ROOT);
		if (name.endsWith(".alg")) {
			return ENGINE_ALG;
		}
		return null;
	}

	public static boolean isShayaSource(String fileName) {
		return engineIdForName(fileName) != null;
	}

	/** Short list for dialogs / warnings. */
	public static String extensionsHint() {
		return ".alg";
	}

	/** One-line engine map for console / refuse messages. */
	public static String enginesHint() {
		return "alg → SCHOOLALGOL (ALG)";
	}

	/** Human-readable engine label for status line / console / About. */
	public static String engineDisplayName(String engineId) {
		if (ENGINE_ALG.equals(engineId)) {
			return "SCHOOLALGOL (ALG)";
		}
		return engineId != null ? engineId : "unknown";
	}

	/**
	 * Check mode: lex + parse via {@code main.py --check} (no execute).
	 */
	public static boolean supportsCheck(String engineId) {
		return ENGINE_ALG.equals(engineId);
	}

	/**
	 * CLI Debug: SCHOOLALGOL has no separate --debug/--trace; Run is the execution path.
	 */
	public static boolean supportsDebug(String engineId) {
		return false;
	}

	/**
	 * Eclipse step-debug UI (SHAYDBG / {@code --debug-protocol}).
	 */
	public static boolean supportsStepDebugUi(String engineId) {
		return ENGINE_ALG.equals(engineId);
	}

	public static String debugRefuseMessage(String engineId) {
		String name = engineDisplayName(engineId);
		return name + " — CLI Debug не поддерживается. Используйте Run / Check / Step Debug.";
	}

	public static String stepDebugRefuseMessage(String engineId) {
		String name = engineDisplayName(engineId);
		return name + " — Eclipse Step Debug (SHAYDBG) недоступен для этого движка.";
	}

	/**
	 * Working directory for the engine (dropins interpreters/SchoolAlgol).
	 */
	public static File getEngineWorkDir(String engineId) {
		String dirName = engineDirName(engineId);
		if (dirName == null) {
			return null;
		}
		File home = getToolchainHome();
		if (home != null) {
			File underInterp = new File(home, "interpreters" + File.separator + dirName);
			if (underInterp.isDirectory()) {
				return underInterp;
			}
			File underHome = new File(home, dirName);
			if (underHome.isDirectory()) {
				return underHome;
			}
		}
		return null;
	}

	/** Entry script {@code main.py}. */
	public static File getEngineEntryScript(String engineId) {
		File cwd = getEngineWorkDir(engineId);
		if (cwd == null) {
			return null;
		}
		String entry = engineEntryScriptName(engineId);
		if (entry == null) {
			return null;
		}
		File script = new File(cwd, entry);
		return script.isFile() ? script : null;
	}

	private static String engineDirName(String engineId) {
		if (ENGINE_ALG.equals(engineId)) {
			return ENGINE_DIR;
		}
		return null;
	}

	private static String engineEntryScriptName(String engineId) {
		if (ENGINE_ALG.equals(engineId)) {
			return "main.py";
		}
		return null;
	}

	/**
	 * Preference-page smoke check: home, wrapper, SchoolAlgol interpreter, Python.
	 * Returns a multi-line human status (never null).
	 */
	public static String validateStatus() {
		StringBuilder sb = new StringBuilder();
		boolean ok = true;

		File home = getToolchainHome();
		if (home == null || !home.isDirectory()) {
			sb.append("FAIL  Toolchain home not found\n");
			sb.append("      Set Preferences → ALG → Toolchain home\n");
			sb.append("      or install dropins/").append(DROPINS_FOLDER).append("/\n");
			ok = false;
		} else {
			sb.append("OK    Toolchain home: ").append(home.getAbsolutePath()).append('\n');
		}

		File wrap = getRunWrapper();
		if (wrap == null || !wrap.isFile()) {
			sb.append("FAIL  tools/shaya-run.bat missing\n");
			ok = false;
		} else {
			sb.append("OK    Wrapper: ").append(wrap.getAbsolutePath()).append('\n');
		}

		if (home != null) {
			File interp = new File(home, "interpreters");
			if (!interp.isDirectory()) {
				sb.append("FAIL  interpreters/ missing under toolchain home\n");
				ok = false;
			} else {
				File school = new File(interp, ENGINE_DIR);
				File mainPy = new File(school, "main.py");
				if (school.isDirectory() && mainPy.isFile()) {
					sb.append("OK    Interpreter: interpreters/").append(ENGINE_DIR)
							.append("/main.py\n");
				} else {
					sb.append("FAIL  interpreters/").append(ENGINE_DIR)
							.append("/main.py missing\n");
					ok = false;
				}
			}
		}

		String pyInfo = probePython();
		sb.append(pyInfo).append('\n');
		if (!pyInfo.startsWith("OK")) {
			ok = false;
		}

		sb.append(ok ? "\nToolchain looks ready." : "\nFix FAIL items, then Validate again.");
		return sb.toString();
	}

	private static String probePython() {
		IPreferenceStore prefs = Activator.getDefault() != null
				? Activator.getDefault().getPreferenceStore() : null;
		String configured = prefs != null ? prefs.getString(ShayaPreferenceConstants.PYTHON_EXECUTABLE) : "";
		if (configured != null && !configured.isBlank()) {
			File f = new File(configured.trim());
			if (f.isFile()) {
				return "OK    Python (prefs): " + f.getAbsolutePath();
			}
			return "FAIL  Python prefs path not a file: " + configured.trim();
		}
		String[] candidates = { "py", "python", "python3" };
		for (String cmd : candidates) {
			try {
				ProcessBuilder pb = cmd.equals("py")
						? new ProcessBuilder("py", "-3", "-c", "import sys; print(sys.executable)")
						: new ProcessBuilder(cmd, "-c", "import sys; print(sys.executable)");
				pb.redirectErrorStream(true);
				Process p = pb.start();
				String out = new String(p.getInputStream().readAllBytes(), java.nio.charset.StandardCharsets.UTF_8)
						.trim();
				int rc = p.waitFor();
				if (rc == 0 && !out.isBlank()) {
					String first = out.lines().findFirst().orElse(out);
					return "OK    Python (PATH/" + cmd + "): " + first;
				}
			} catch (Exception ignored) {
			}
		}
		return "FAIL  Python 3 not found (set Preferences → ALG → Python, or PATH / py -3)";
	}
}
