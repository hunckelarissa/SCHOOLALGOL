package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IContainer;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceProxy;
import org.eclipse.core.resources.IResourceProxyVisitor;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.dialogs.ElementListSelectionDialog;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.part.FileEditorInput;
import org.eclipse.ui.texteditor.ITextEditor;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/** Lightweight Find References: scan project (or file) for the identifier under the cursor. */
public class ShayaFindReferencesHandler extends AbstractHandler {

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
			MessageDialog.openInformation(shell, "Find References", "Place the cursor on an identifier.");
			return null;
		}
		if (ShayaKeywords.isKeyword(word, editor.currentDialect())) {
			MessageDialog.openInformation(shell, "Find References",
					"\"" + word + "\" is a keyword / builtin.\n"
							+ "Find References targets user identifiers only\n"
							+ "(comments and string literals are skipped).");
			return null;
		}
		IFile file = null;
		if (editor.getEditorInput() instanceof FileEditorInput) {
			file = ((FileEditorInput) editor.getEditorInput()).getFile();
		}
		if (file == null) {
			MessageDialog.openInformation(shell, "Find References", "Save the file into a project first.");
			return null;
		}
		boolean projectScope = MessageDialog.openQuestion(shell, "Find References",
				"Search whole project for \"" + word + "\"?\n"
						+ "(Same engine only — extension → engine law.\nNo = current file only)");
		List<Hit> hits = new ArrayList<>();
		try {
			String engine = ShayaToolchain.engineIdForName(file.getName());
			if (projectScope) {
				scanContainer(file.getProject(), word, engine, hits);
			} else {
				scanFile(file, word, hits);
			}
		} catch (CoreException e) {
			MessageDialog.openError(shell, "Find References", e.getMessage());
			return null;
		}
		if (hits.isEmpty()) {
			MessageDialog.openInformation(shell, "Find References", "No references to \"" + word + "\".");
			return null;
		}
		ElementListSelectionDialog dlg = new ElementListSelectionDialog(shell, new LabelProvider());
		dlg.setTitle("References to " + word);
		dlg.setMessage(hits.size() + " hit(s) — select to open:");
		dlg.setElements(hits.toArray());
		if (dlg.open() != Window.OK) {
			return null;
		}
		Object sel = dlg.getFirstResult();
		if (sel instanceof Hit) {
			Hit h = (Hit) sel;
			try {
				IEditorPart opened = IDE.openEditor(editor.getSite().getPage(), h.file, true);
				if (opened instanceof ITextEditor) {
					ITextEditor te = (ITextEditor) opened;
					IDocument d = te.getDocumentProvider().getDocument(opened.getEditorInput());
					if (d != null && h.line >= 1 && h.line <= d.getNumberOfLines()) {
						int off = d.getLineOffset(h.line - 1);
						int len = d.getLineLength(h.line - 1);
						te.selectAndReveal(off, Math.max(0, len - 1));
					}
				}
			} catch (Exception ignored) {
			}
		}
		return null;
	}

	private static void scanContainer(IContainer container, String word, String engineId, List<Hit> hits)
			throws CoreException {
		container.accept(new IResourceProxyVisitor() {
			@Override
			public boolean visit(IResourceProxy proxy) throws CoreException {
				if (proxy.getType() == IResource.FILE && ShayaToolchain.isShayaSource(proxy.getName())) {
					if (engineId != null && !engineId.equals(ShayaToolchain.engineIdForName(proxy.getName()))) {
						return true;
					}
					IResource r = proxy.requestResource();
					if (r instanceof IFile) {
						scanFile((IFile) r, word, hits);
					}
				}
				return true;
			}
		}, IResource.NONE);
	}

	private static void scanFile(IFile file, String word, List<Hit> hits) throws CoreException {
		java.io.InputStream in = file.getContents(true);
		String text;
		try {
			text = new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
		} catch (Exception e) {
			return;
		} finally {
			try {
				in.close();
			} catch (Exception ignored) {
			}
		}
		boolean[] mask = ShayaLexicalMask.mask(text,
				ShayaCommentStyle.forDialect(ShayaKeywords.dialectOfFileName(file.getName())));
		String lower = text.toLowerCase(Locale.ROOT);
		String w = word.toLowerCase(Locale.ROOT);
		int from = 0;
		while (from < lower.length()) {
			int idx = lower.indexOf(w, from);
			if (idx < 0) {
				break;
			}
			boolean left = idx == 0 || !ShayaIdentifiers.isIdentPart(text.charAt(idx - 1));
			int end = idx + word.length();
			boolean right = end >= text.length() || !ShayaIdentifiers.isIdentPart(text.charAt(end));
			if (left && right && !ShayaLexicalMask.covered(mask, idx)) {
				int line = 1;
				for (int p = 0; p < idx; p++) {
					char c = text.charAt(p);
					if (c == '\n') {
						line++;
					} else if (c == '\r') {
						line++;
						if (p + 1 < idx && text.charAt(p + 1) == '\n') {
							p++;
						}
					}
				}
				int lineStart = idx;
				while (lineStart > 0 && text.charAt(lineStart - 1) != '\n' && text.charAt(lineStart - 1) != '\r') {
					lineStart--;
				}
				int lineEnd = idx;
				while (lineEnd < text.length() && text.charAt(lineEnd) != '\n' && text.charAt(lineEnd) != '\r') {
					lineEnd++;
				}
				hits.add(new Hit(file, line, text.substring(lineStart, lineEnd).trim()));
				from = end;
				continue;
			}
			from = idx + 1;
		}
	}

	private static final class Hit {
		final IFile file;
		final int line;
		final String text;

		Hit(IFile file, int line, String text) {
			this.file = file;
			this.line = line;
			this.text = text;
		}

		@Override
		public String toString() {
			return file.getProjectRelativePath() + ":" + line + "  " + text;
		}
	}
}
