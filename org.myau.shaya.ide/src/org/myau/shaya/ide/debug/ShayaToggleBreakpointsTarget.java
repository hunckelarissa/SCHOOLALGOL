package org.myau.shaya.ide.debug;

import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.debug.ui.actions.IToggleBreakpointsTarget;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchPart;
import org.eclipse.ui.texteditor.ITextEditor;

/**
 * Ctrl+Shift+B / Toggle Breakpoint для редактора ALG.
 */
public class ShayaToggleBreakpointsTarget implements IToggleBreakpointsTarget {

	@Override
	public void toggleLineBreakpoints(IWorkbenchPart part, ISelection selection) throws CoreException {
		IResource resource = resourceOf(part);
		if (resource == null || !(selection instanceof ITextSelection)) {
			return;
		}
		int line = ((ITextSelection) selection).getStartLine() + 1;
		if (line < 1) {
			return;
		}
		ShayaBreakpoints.toggleLine(resource, line);
	}

	@Override
	public boolean canToggleLineBreakpoints(IWorkbenchPart part, ISelection selection) {
		return resourceOf(part) != null && selection instanceof ITextSelection;
	}

	@Override
	public void toggleMethodBreakpoints(IWorkbenchPart part, ISelection selection) {
	}

	@Override
	public boolean canToggleMethodBreakpoints(IWorkbenchPart part, ISelection selection) {
		return false;
	}

	@Override
	public void toggleWatchpoints(IWorkbenchPart part, ISelection selection) {
	}

	@Override
	public boolean canToggleWatchpoints(IWorkbenchPart part, ISelection selection) {
		return false;
	}

	private static IResource resourceOf(IWorkbenchPart part) {
		if (!(part instanceof IEditorPart)) {
			return null;
		}
		IEditorPart editor = (IEditorPart) part;
		if (!(editor instanceof ITextEditor)) {
			return null;
		}
		Object input = editor.getEditorInput();
		if (input instanceof org.eclipse.ui.IFileEditorInput) {
			return ((org.eclipse.ui.IFileEditorInput) input).getFile();
		}
		return null;
	}
}
