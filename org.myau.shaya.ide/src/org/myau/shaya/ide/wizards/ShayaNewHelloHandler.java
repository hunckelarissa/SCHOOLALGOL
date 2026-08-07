package org.myau.shaya.ide.wizards;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IContainer;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.Path;
import org.eclipse.jface.dialogs.IInputValidator;
import org.eclipse.jface.dialogs.InputDialog;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.dialogs.ElementListSelectionDialog;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.ide.IDE;

/**
 * ALG → New Hello… — pick extension/engine, create Hello.&lt;ext&gt; in selected folder.
 */
public class ShayaNewHelloHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		Shell shell = HandlerUtil.getActiveShell(event);
		if (shell == null) {
			return null;
		}
		IContainer folder = resolveFolder(event);
		if (folder == null) {
			org.eclipse.jface.dialogs.MessageDialog.openInformation(shell, "New Hello",
					"Select a project or folder in the Project Explorer first.");
			return null;
		}
		ElementListSelectionDialog pick = new ElementListSelectionDialog(shell, new LabelProvider());
		pick.setTitle("New Hello");
		pick.setMessage("Choose extension → engine (product law):");
		pick.setElements(ShayaHelloBodies.all());
		if (pick.open() != Window.OK || !(pick.getFirstResult() instanceof ShayaHelloBodies.Spec)) {
			return null;
		}
		ShayaHelloBodies.Spec d = (ShayaHelloBodies.Spec) pick.getFirstResult();
		InputDialog nameDlg = new InputDialog(shell, "New Hello", "File name (without extension):", "Hello",
				new IInputValidator() {
					@Override
					public String isValid(String newText) {
						if (newText == null || newText.trim().isEmpty()) {
							return "Name required";
						}
						if (!newText.matches("[A-Za-zА-Яа-яЁё][A-Za-z0-9_А-Яа-яЁё]*")) {
							return "Use an identifier-like name";
						}
						return null;
					}
				});
		if (nameDlg.open() != Window.OK) {
			return null;
		}
		String stem = nameDlg.getValue().trim();
		String fileName = stem + "." + d.ext;
		IFile file = folder.getFile(new Path(fileName));
		if (file.exists()) {
			org.eclipse.jface.dialogs.MessageDialog.openError(shell, "New Hello", fileName + " already exists.");
			return null;
		}
		try {
			file.create(new ByteArrayInputStream(d.body.getBytes(StandardCharsets.UTF_8)), true, null);
			ShayaWizardSupport.ensureNature(file);
			IDE.openEditor(HandlerUtil.getActiveWorkbenchWindow(event).getActivePage(), file);
		} catch (Exception e) {
			org.eclipse.jface.dialogs.MessageDialog.openError(shell, "New Hello", e.getMessage());
		}
		return null;
	}

	private static IContainer resolveFolder(ExecutionEvent event) {
		IStructuredSelection sel = HandlerUtil.getCurrentStructuredSelection(event);
		if (sel == null || sel.isEmpty()) {
			return null;
		}
		Object first = sel.getFirstElement();
		if (first instanceof IContainer) {
			return (IContainer) first;
		}
		if (first instanceof IFile) {
			return ((IFile) first).getParent();
		}
		if (first instanceof IResource) {
			IResource r = (IResource) first;
			if (r instanceof IContainer) {
				return (IContainer) r;
			}
			return r.getParent();
		}
		return null;
	}
}
