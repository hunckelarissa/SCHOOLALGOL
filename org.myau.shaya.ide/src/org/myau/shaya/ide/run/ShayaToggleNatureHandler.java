package org.myau.shaya.ide.run;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IFileEditorInput;
import org.eclipse.ui.handlers.HandlerUtil;
import org.myau.shaya.ide.nature.ShayaNatureSupport;

/** ALG → Add/Remove ALG Project Nature. */
public class ShayaToggleNatureHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		IProject project = resolveProject(event);
		if (project == null || !project.isAccessible()) {
			MessageDialog.openWarning(HandlerUtil.getActiveShell(event), "ALG",
					"Select a project (or open a file inside it).");
			return null;
		}
		try {
			boolean had = ShayaNatureSupport.hasNature(project);
			ShayaNatureSupport.toggleNature(project);
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG",
					had
							? "Removed ALG nature from: " + project.getName()
							: "Added ALG nature (+ check builder) to: " + project.getName());
		} catch (Exception e) {
			MessageDialog.openError(HandlerUtil.getActiveShell(event), "ALG",
					"Nature change failed: " + e.getMessage());
		}
		return null;
	}

	private static IProject resolveProject(ExecutionEvent event) {
		ISelection sel = HandlerUtil.getCurrentSelection(event);
		if (sel instanceof IStructuredSelection) {
			Object el = ((IStructuredSelection) sel).getFirstElement();
			if (el instanceof IProject) {
				return (IProject) el;
			}
			if (el instanceof IResource) {
				return ((IResource) el).getProject();
			}
		}
		IEditorPart editor = HandlerUtil.getActiveEditor(event);
		if (editor != null && editor.getEditorInput() instanceof IFileEditorInput) {
			return ((IFileEditorInput) editor.getEditorInput()).getFile().getProject();
		}
		return null;
	}
}
