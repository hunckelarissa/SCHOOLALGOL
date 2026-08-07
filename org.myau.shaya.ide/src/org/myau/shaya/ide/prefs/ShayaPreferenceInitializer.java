package org.myau.shaya.ide.prefs;

import org.eclipse.core.runtime.preferences.AbstractPreferenceInitializer;
import org.eclipse.jface.preference.IPreferenceStore;
import org.myau.shaya.ide.Activator;

public class ShayaPreferenceInitializer extends AbstractPreferenceInitializer {

	@Override
	public void initializeDefaultPreferences() {
		IPreferenceStore store = Activator.getDefault().getPreferenceStore();
		store.setDefault(ShayaPreferenceConstants.TOOLCHAIN_HOME, "");
		store.setDefault(ShayaPreferenceConstants.EXTRA_ARGS, "");
		store.setDefault(ShayaPreferenceConstants.PYTHON_EXECUTABLE, "");
		store.setDefault(ShayaPreferenceConstants.CHECK_ON_SAVE, false);
		store.setDefault(ShayaPreferenceConstants.INDENT_WIDTH, 2);
		store.setDefault(ShayaPreferenceConstants.INSERT_SPACES, true);
	}
}
