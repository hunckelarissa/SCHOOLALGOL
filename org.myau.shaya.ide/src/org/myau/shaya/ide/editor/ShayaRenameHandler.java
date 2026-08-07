package org.myau.shaya.ide.editor;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IContainer;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceProxy;
import org.eclipse.core.resources.IResourceProxyVisitor;
import org.eclipse.core.resources.IWorkspaceRunnable;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.NullProgressMonitor;
import org.eclipse.jface.dialogs.IInputValidator;
import org.eclipse.jface.dialogs.InputDialog;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.part.FileEditorInput;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/** Lightweight Rename: replace whole-word identifier in the current file or project. */
public class ShayaRenameHandler extends AbstractHandler {

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
		String oldName = ShayaIdentifiers.wordAt(editor, doc);
		if (oldName == null || oldName.isEmpty()) {
			MessageDialog.openInformation(shell, "Rename", "Place the cursor on an identifier.");
			return null;
		}
		final ShayaKeywords.Dialect dialect = editor.currentDialect();
		if (ShayaKeywords.isKeyword(oldName, dialect)) {
			MessageDialog.openWarning(shell, "Rename",
					"\"" + oldName + "\" is a keyword / builtin for this dialect.\n"
							+ "Rename refuses reserved words.");
			return null;
		}
		InputDialog nameDlg = new InputDialog(shell, "Rename", "Rename \"" + oldName + "\" to:", oldName,
				new IInputValidator() {
					@Override
					public String isValid(String newText) {
						if (newText == null || newText.trim().isEmpty()) {
							return "Name required";
						}
						String t = newText.trim();
						if (t.equals(oldName)) {
							return "Same name";
						}
						if (!ShayaIdentifiers.isIdentName(t)) {
							return "Use identifier-like name (letters, digits, _)";
						}
						if (ShayaKeywords.isKeyword(t, dialect)) {
							return "New name is a keyword / builtin";
						}
						return null;
					}
				});
		if (nameDlg.open() != Window.OK) {
			return null;
		}
		String newName = nameDlg.getValue().trim();
		boolean project = MessageDialog.openQuestion(shell, "Rename",
				"Rename in whole project?\n(No = current file only)");

		IFile current = null;
		if (editor.getEditorInput() instanceof FileEditorInput) {
			current = ((FileEditorInput) editor.getEditorInput()).getFile();
		}

		List<PreviewRow> preview = new ArrayList<>();
		try {
			if (!project || current == null || current.getProject() == null) {
				int n = countWords(doc.get(), oldName, ShayaCommentStyle.forDialect(dialect));
				if (n > 0) {
					preview.add(new PreviewRow(current != null ? current.getName() : "(editor)", n));
				}
			} else {
				for (IFile file : collectShayaFiles(current.getProject())) {
					int n;
					if (file.equals(current)) {
						n = countWords(doc.get(), oldName, ShayaCommentStyle.forDialect(dialect));
					} else {
						n = countInFile(file, oldName);
					}
					if (n > 0) {
						preview.add(new PreviewRow(file.getProjectRelativePath().toString(), n));
					}
				}
			}
		} catch (Exception e) {
			MessageDialog.openError(shell, "Rename", e.getMessage());
			return null;
		}
		if (preview.isEmpty()) {
			MessageDialog.openInformation(shell, "Rename", "No occurrences of \"" + oldName + "\".");
			return null;
		}
		int total = 0;
		StringBuilder msg = new StringBuilder();
		msg.append("Rename \"").append(oldName).append("\" → \"").append(newName).append("\"?\n\n");
		int shown = 0;
		for (PreviewRow row : preview) {
			total += row.count;
			if (shown < 12) {
				msg.append("  ").append(row.path).append(" — ").append(row.count).append('\n');
				shown++;
			}
		}
		if (preview.size() > shown) {
			msg.append("  … and ").append(preview.size() - shown).append(" more file(s)\n");
		}
		msg.append('\n').append(total).append(" occurrence(s) in ").append(preview.size()).append(" file(s).");
		if (!MessageDialog.openConfirm(shell, "Rename preview", msg.toString())) {
			return null;
		}

		final IFile currentFile = current;
		final int[] stats = new int[2];
		try {
			ResourcesPlugin.getWorkspace().run((IWorkspaceRunnable) monitor -> {
				try {
					if (!project || currentFile == null || currentFile.getProject() == null) {
						int n = replaceInDocument(doc, oldName, newName, dialect);
						stats[0] = n;
						stats[1] = n > 0 ? 1 : 0;
					} else {
						for (IFile file : collectShayaFiles(currentFile.getProject())) {
							int n;
							if (file.equals(currentFile)) {
								n = replaceInDocument(doc, oldName, newName, dialect);
							} else {
								n = replaceInFile(file, oldName, newName);
							}
							if (n > 0) {
								stats[1]++;
								stats[0] += n;
							}
						}
					}
				} catch (Exception e) {
					throw new CoreException(new org.eclipse.core.runtime.Status(
							org.eclipse.core.runtime.IStatus.ERROR, "org.myau.shaya.ide", e.getMessage(), e));
				}
			}, new NullProgressMonitor());
		} catch (CoreException e) {
			MessageDialog.openError(shell, "Rename", e.getMessage());
			return null;
		}
		MessageDialog.openInformation(shell, "Rename",
				"Renamed \"" + oldName + "\" → \"" + newName + "\"\n" + stats[0] + " occurrence(s) in "
						+ stats[1] + " file(s).");
		return null;
	}

	private static int countInFile(IFile file, String oldName) throws Exception {
		byte[] bytes;
		try (java.io.InputStream in = file.getContents(true)) {
			bytes = in.readAllBytes();
		}
		String text = new String(bytes, StandardCharsets.UTF_8);
		return countWords(text, oldName, ShayaCommentStyle.forDialect(ShayaKeywords.dialectOfFileName(file.getName())));
	}

	private static int replaceInDocument(IDocument doc, String oldName, String newName, ShayaKeywords.Dialect dialect)
			throws Exception {
		String text = doc.get();
		ShayaCommentStyle style = ShayaCommentStyle.forDialect(dialect);
		String replaced = replaceWords(text, oldName, newName, style);
		if (replaced.equals(text)) {
			return 0;
		}
		int count = countWords(text, oldName, style);
		doc.replace(0, text.length(), replaced);
		return count;
	}

	private static int replaceInFile(IFile file, String oldName, String newName) throws Exception {
		byte[] bytes;
		try (java.io.InputStream in = file.getContents(true)) {
			bytes = in.readAllBytes();
		}
		String text = new String(bytes, StandardCharsets.UTF_8);
		ShayaCommentStyle style = ShayaCommentStyle.forDialect(ShayaKeywords.dialectOfFileName(file.getName()));
		String replaced = replaceWords(text, oldName, newName, style);
		if (replaced.equals(text)) {
			return 0;
		}
		int count = countWords(text, oldName, style);
		file.setContents(new ByteArrayInputStream(replaced.getBytes(StandardCharsets.UTF_8)), true, true, null);
		return count;
	}

	static String replaceWords(String text, String oldName, String newName, ShayaCommentStyle style) {
		boolean[] mask = ShayaLexicalMask.mask(text, style);
		StringBuilder sb = new StringBuilder(text.length() + 16);
		int i = 0;
		while (i < text.length()) {
			if (!ShayaLexicalMask.covered(mask, i) && ShayaIdentifiers.isIdentStart(text.charAt(i))) {
				int start = i;
				i++;
				while (i < text.length() && ShayaIdentifiers.isIdentPart(text.charAt(i))) {
					i++;
				}
				String word = text.substring(start, i);
				sb.append(word.equals(oldName) ? newName : word);
			} else {
				sb.append(text.charAt(i));
				i++;
			}
		}
		return sb.toString();
	}

	static int countWords(String text, String name, ShayaCommentStyle style) {
		boolean[] mask = ShayaLexicalMask.mask(text, style);
		int count = 0;
		int i = 0;
		while (i < text.length()) {
			if (!ShayaLexicalMask.covered(mask, i) && ShayaIdentifiers.isIdentStart(text.charAt(i))) {
				int start = i;
				i++;
				while (i < text.length() && ShayaIdentifiers.isIdentPart(text.charAt(i))) {
					i++;
				}
				if (text.substring(start, i).equals(name)) {
					count++;
				}
			} else {
				i++;
			}
		}
		return count;
	}

	private static Set<IFile> collectShayaFiles(IContainer root) throws CoreException {
		Set<IFile> files = new LinkedHashSet<>();
		root.accept(new IResourceProxyVisitor() {
			@Override
			public boolean visit(IResourceProxy proxy) {
				if (proxy.getType() == IResource.FILE && ShayaToolchain.isShayaSource(proxy.getName())) {
					IResource r = proxy.requestResource();
					if (r instanceof IFile) {
						files.add((IFile) r);
					}
				}
				return true;
			}
		}, IResource.NONE);
		return files;
	}

	private static final class PreviewRow {
		final String path;
		final int count;

		PreviewRow(String path, int count) {
			this.path = path;
			this.count = count;
		}
	}
}
