package org.myau.shaya.ide.run;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IWorkspaceRoot;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.NullProgressMonitor;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IFileEditorInput;
import org.eclipse.ui.handlers.HandlerUtil;

/**
 * Refresh project / workspace so files created on disk appear in Project Explorer.
 */
public class ShayaRefreshHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		try {
			IProject project = resolveProject(event);
			if (project != null && project.isAccessible()) {
				project.refreshLocal(IResource.DEPTH_INFINITE, new NullProgressMonitor());
				MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG",
						"Refreshed project: " + project.getName());
				return null;
			}
			IWorkspaceRoot root = ResourcesPlugin.getWorkspace().getRoot();
			root.refreshLocal(IResource.DEPTH_INFINITE, new NullProgressMonitor());
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG",
					"Refreshed entire workspace.");
		} catch (Exception e) {
			MessageDialog.openError(HandlerUtil.getActiveShell(event), "ALG",
					"Refresh failed: " + e.getMessage());
		}
		return null;
	}

	private static IProject resolveProject(ExecutionEvent event) {
		IEditorPart editor = HandlerUtil.getActiveEditor(event);
		if (editor != null && editor.getEditorInput() instanceof IFileEditorInput) {
			return ((IFileEditorInput) editor.getEditorInput()).getFile().getProject();
		}
		ISelection sel = HandlerUtil.getCurrentSelection(event);
		if (sel instanceof IStructuredSelection) {
			Object el = ((IStructuredSelection) sel).getFirstElement();
			if (el instanceof IResource) {
				return ((IResource) el).getProject();
			}
		}
		return null;
	}
}
