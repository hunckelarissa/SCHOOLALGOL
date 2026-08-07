package org.myau.shaya.ide.editor;

import java.util.List;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IFile;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.dialogs.ElementListSelectionDialog;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.part.FileEditorInput;

/** Go to Declaration (F3). */
public class ShayaGotoDeclarationHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		IEditorPart part = HandlerUtil.getActiveEditor(event);
		if (!(part instanceof ShayaEditor)) {
			return null;
		}
		ShayaEditor editor = (ShayaEditor) part;
		IDocument doc = editor.getEditorDocument();
		Shell shell = HandlerUtil.getActiveShell(event);
		if (doc == null || shell == null) {
			return null;
		}
		String word = ShayaIdentifiers.wordAt(editor, doc);
		if (word == null || word.isEmpty()) {
			MessageDialog.openInformation(shell, "Go to Declaration", "Place the cursor on an identifier.");
			return null;
		}
		IFile file = null;
		if (editor.getEditorInput() instanceof FileEditorInput) {
			file = ((FileEditorInput) editor.getEditorInput()).getFile();
		}
		List<ShayaDeclarations.Hit> hits = ShayaDeclarations.findDeclarations(doc, file, word, true);
		if (hits.isEmpty()) {
			MessageDialog.openInformation(shell, "Go to Declaration",
					"No declaration found for \"" + word + "\".");
			return null;
		}
		ShayaDeclarations.Hit chosen = hits.get(0);
		if (hits.size() > 1) {
			ElementListSelectionDialog dlg = new ElementListSelectionDialog(shell, new LabelProvider());
			dlg.setTitle("Go to Declaration — " + word);
			dlg.setMessage("Multiple declarations:");
			dlg.setElements(hits.toArray());
			if (dlg.open() != Window.OK || !(dlg.getFirstResult() instanceof ShayaDeclarations.Hit)) {
				return null;
			}
			chosen = (ShayaDeclarations.Hit) dlg.getFirstResult();
		}
		ShayaDeclarations.openHit(editor, chosen);
		return null;
	}
}
