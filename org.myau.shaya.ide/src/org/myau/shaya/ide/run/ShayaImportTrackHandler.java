package org.myau.shaya.ide.run;

import java.io.File;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IProjectDescription;
import org.eclipse.core.resources.IWorkspace;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.NullProgressMonitor;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.ide.IDE;
import org.myau.shaya.ide.nature.ShayaNatureSupport;
import org.myau.shaya.ide.toolchain.ShayaDocs;

/**
 * Import examples/track as a linked Eclipse project "shaya-track".
 */
public class ShayaImportTrackHandler extends AbstractHandler {

	public static final String PROJECT_NAME = "shaya-track";

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		File track = ShayaDocs.findTrackDir();
		if (track == null || !track.isDirectory()) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "Import Track",
					"examples/track not found under the ALG toolchain.\n"
							+ "Install dropins/schoolalgol-shaya or set Preferences → ALG → Toolchain home.");
			return null;
		}
		try {
			IWorkspace ws = ResourcesPlugin.getWorkspace();
			IProject project = ws.getRoot().getProject(PROJECT_NAME);
			if (!project.exists()) {
				IProjectDescription desc = ws.newProjectDescription(PROJECT_NAME);
				desc.setLocationURI(track.toURI());
				project.create(desc, new NullProgressMonitor());
			}
			if (!project.isOpen()) {
				project.open(new NullProgressMonitor());
			}
			ShayaNatureSupport.addNature(project);
			project.refreshLocal(org.eclipse.core.resources.IResource.DEPTH_INFINITE,
					new NullProgressMonitor());

			org.eclipse.core.resources.IFile readme = project.getFile("README.md");
			if (readme.exists()) {
				IDE.openEditor(HandlerUtil.getActiveWorkbenchWindow(event).getActivePage(), readme);
			}
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "Import Track",
					"Project \"" + PROJECT_NAME + "\" ready.\n"
							+ "Location: " + track.getAbsolutePath());
		} catch (Exception e) {
			MessageDialog.openError(HandlerUtil.getActiveShell(event), "Import Track",
					e.getMessage());
		}
		return null;
	}
}
