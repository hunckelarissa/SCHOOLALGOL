package org.myau.shaya.ide.i18n;

import org.eclipse.osgi.util.NLS;

/**
 * Eclipse NLS catalog for ALG IDE UI (default EN + messages_ru.properties).
 */
public class Messages extends NLS {

	private static final String BUNDLE_NAME = "org.myau.shaya.ide.i18n.messages";

	// —— Welcome ——
	public static String Welcome_shellTitle;
	public static String Welcome_brand;
	public static String Welcome_tip;
	public static String Welcome_newProject;
	public static String Welcome_importTrack;
	public static String Welcome_shortcuts;
	public static String Welcome_errorTitle;
	public static String Welcome_wizardMissing;

	// —— About ——
	public static String About_shellTitle;
	public static String About_title;
	public static String About_body;
	public static String About_cmds;
	public static String About_meta;
	public static String About_grammarButton;
	public static String About_trackButton;
	public static String About_grammarMissingTitle;
	public static String About_grammarMissing;
	public static String About_trackMissingTitle;
	public static String About_trackMissing;
	public static String About_toolchainNotFound;

	// —— Shortcuts ——
	public static String Shortcuts_shellTitle;
	public static String Shortcuts_body;

	// —— Grammar / Track handlers ——
	public static String Grammar_title;
	public static String Grammar_missing;
	public static String Track_title;
	public static String Track_missing;

	// —— Debug handler ——
	public static String Alg_title;
	public static String Alg_openSource;
	public static String Alg_unknownExtension;
	public static String Alg_debugTitle;

	// —— Markers ——
	public static String Markers_failMessage;
	public static String Markers_tipPrefix;
	public static String Markers_tip_algBlock;
	public static String Markers_tip_undeclared;
	public static String Markers_tip_type;
	public static String Markers_tip_index;
	public static String Markers_tip_module;
	public static String Markers_tip_python;
	public static String Markers_tip_toolchain;
	public static String Markers_tip_extension;

	// —— Toolchain ——
	public static String Toolchain_debugRefuse;
	public static String Toolchain_stepDebugRefuse;
	public static String Toolchain_validate_homeMissing;
	public static String Toolchain_validate_homeOk;
	public static String Toolchain_validate_wrapperMissing;
	public static String Toolchain_validate_wrapperOk;
	public static String Toolchain_validate_interpMissing;
	public static String Toolchain_validate_interpOk;
	public static String Toolchain_validate_mainMissing;
	public static String Toolchain_validate_pythonPrefsOk;
	public static String Toolchain_validate_pythonPrefsBad;
	public static String Toolchain_validate_pythonPathOk;
	public static String Toolchain_validate_pythonNotFound;
	public static String Toolchain_validate_ready;
	public static String Toolchain_validate_fix;

	// —— Preferences ——
	public static String Prefs_description;
	public static String Prefs_toolchainHome;
	public static String Prefs_extraArgs;
	public static String Prefs_python;
	public static String Prefs_indentWidth;
	public static String Prefs_insertSpaces;
	public static String Prefs_checkOnSave;
	public static String Prefs_showWelcome;
	public static String Prefs_validateButton;
	public static String Prefs_clearRecentButton;
	public static String Prefs_validateTitle;
	public static String Prefs_clearTitle;
	public static String Prefs_clearMessage;

	static {
		NLS.initializeMessages(BUNDLE_NAME, Messages.class);
	}

	private Messages() {
	}
}
