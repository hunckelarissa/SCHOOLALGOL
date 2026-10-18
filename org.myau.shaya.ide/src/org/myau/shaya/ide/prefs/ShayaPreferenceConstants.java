package org.myau.shaya.ide.prefs;

public final class ShayaPreferenceConstants {

	private ShayaPreferenceConstants() {
	}

	/** Override path to dropins/schoolalgol-shaya (empty = auto-detect). */
	public static final String TOOLCHAIN_HOME = "toolchainHome";

	/** Extra args passed to tools/shaya-run.bat. */
	public static final String EXTRA_ARGS = "extraArgs";

	/** Optional absolute path to python.exe (sets SHAYA_PYTHON for the wrapper). */
	public static final String PYTHON_EXECUTABLE = "pythonExecutable";

	/** Run --check on save (async, markers). Default off. */
	public static final String CHECK_ON_SAVE = "checkOnSave";

	/** Indent width in spaces (2 or 4). Used when {@link #INSERT_SPACES} is true. */
	public static final String INDENT_WIDTH = "indentWidth";

	/** If true, indent with spaces; if false, use a single tab. */
	public static final String INSERT_SPACES = "insertSpacesForTabs";

	/** Show Welcome dialog once after workbench start (then cleared). */
	public static final String SHOW_WELCOME_ON_STARTUP = "showWelcomeOnStartup";
}
