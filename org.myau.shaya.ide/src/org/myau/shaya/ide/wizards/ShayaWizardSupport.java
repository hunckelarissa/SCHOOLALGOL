package org.myau.shaya.ide.wizards;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IProject;
import org.myau.shaya.ide.nature.ShayaNatureSupport;

/** Shared helpers for New Project / New Hello wizards. */
public final class ShayaWizardSupport {

	private ShayaWizardSupport() {
	}

	public static void ensureNature(IFile file) {
		if (file == null) {
			return;
		}
		IProject project = file.getProject();
		if (project == null || !project.isAccessible()) {
			return;
		}
		try {
			ShayaNatureSupport.addNature(project);
		} catch (Exception ignored) {
		}
	}
}
