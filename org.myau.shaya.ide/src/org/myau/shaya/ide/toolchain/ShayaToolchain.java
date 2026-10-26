package org.myau.shaya.ide.toolchain;

import java.io.File;
import java.net.URI;
import java.net.URL;
import java.util.Locale;

import org.eclipse.core.runtime.FileLocator;
import org.eclipse.core.runtime.Platform;
import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.osgi.util.NLS;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.i18n.Messages;
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
	 * Transpile to C via {@code main.py --transpile}.
	 */
	public static boolean supportsTranspile(String engineId) {
		return ENGINE_ALG.equals(engineId);
	}

	/**
	 * Legacy CLI Debug: not supported (use Step Debug / SHAYDBG).
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
		return NLS.bind(Messages.Toolchain_debugRefuse, engineDisplayName(engineId));
	}

	public static String stepDebugRefuseMessage(String engineId) {
		return NLS.bind(Messages.Toolchain_stepDebugRefuse, engineDisplayName(engineId));
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
			sb.append(NLS.bind(Messages.Toolchain_validate_homeMissing, DROPINS_FOLDER));
			ok = false;
		} else {
			sb.append(NLS.bind(Messages.Toolchain_validate_homeOk, home.getAbsolutePath()));
		}

		File wrap = getRunWrapper();
		if (wrap == null || !wrap.isFile()) {
			sb.append(Messages.Toolchain_validate_wrapperMissing);
			ok = false;
		} else {
			sb.append(NLS.bind(Messages.Toolchain_validate_wrapperOk, wrap.getAbsolutePath()));
		}

		if (home != null) {
			File interp = new File(home, "interpreters");
			if (!interp.isDirectory()) {
				sb.append(Messages.Toolchain_validate_interpMissing);
				ok = false;
			} else {
				File school = new File(interp, ENGINE_DIR);
				File mainPy = new File(school, "main.py");
				if (school.isDirectory() && mainPy.isFile()) {
					sb.append(NLS.bind(Messages.Toolchain_validate_interpOk, ENGINE_DIR));
				} else {
					sb.append(NLS.bind(Messages.Toolchain_validate_mainMissing, ENGINE_DIR));
					ok = false;
				}
			}
		}

		String pyInfo = probePython();
		sb.append(pyInfo).append('\n');
		if (!pyInfo.startsWith("OK")) {
			ok = false;
		}

		sb.append(ok ? Messages.Toolchain_validate_ready : Messages.Toolchain_validate_fix);
		return sb.toString();
	}

	private static String probePython() {
		IPreferenceStore prefs = Activator.getDefault() != null
				? Activator.getDefault().getPreferenceStore() : null;
		String configured = prefs != null ? prefs.getString(ShayaPreferenceConstants.PYTHON_EXECUTABLE) : "";
		if (configured != null && !configured.isBlank()) {
			File f = new File(configured.trim());
			if (f.isFile()) {
				return NLS.bind(Messages.Toolchain_validate_pythonPrefsOk, f.getAbsolutePath());
			}
			return NLS.bind(Messages.Toolchain_validate_pythonPrefsBad, configured.trim());
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
					return NLS.bind(Messages.Toolchain_validate_pythonPathOk, cmd, first);
				}
			} catch (Exception ignored) {
			}
		}
		return Messages.Toolchain_validate_pythonNotFound;
	}
}
