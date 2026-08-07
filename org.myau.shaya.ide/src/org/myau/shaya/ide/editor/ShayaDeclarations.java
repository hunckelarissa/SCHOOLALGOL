package org.myau.shaya.ide.editor;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.core.resources.IContainer;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceProxy;
import org.eclipse.core.resources.IResourceProxyVisitor;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.Region;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.part.FileEditorInput;
import org.eclipse.ui.texteditor.ITextEditor;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * Shared declaration search for Go to Declaration / Ctrl+Click.
 * Project scope is limited to the same engine (extension → engine law).
 */
public final class ShayaDeclarations {

	private static final Pattern[] DEF_PATTERNS = {
			Pattern.compile("(?iu)^\\s*алг\\s+(\\w+)"),
			Pattern.compile("(?iu)^\\s*проц\\s+(\\w+)"),
			Pattern.compile("(?iu)^\\s*функ\\s+(\\w+)"),
			Pattern.compile("(?iu)^\\s*модуль\\s+(\\w+)"),
			Pattern.compile("(?i)^\\s*alg\\s+(\\w+)"),
			Pattern.compile("(?i)^\\s*proc\\s+(\\w+)"),
			Pattern.compile("(?i)^\\s*func\\s+(\\w+)"),
			Pattern.compile("(?i)^\\s*module\\s+(\\w+)")
	};

	private ShayaDeclarations() {
	}

	public static final class Hit {
		public final IFile file;
		public final int line;
		public final int offset;
		public final int length;
		public final String text;
		public final String name;

		public Hit(IFile file, int line, int offset, int length, String text, String name) {
			this.file = file;
			this.line = line;
			this.offset = offset;
			this.length = length;
			this.text = text;
			this.name = name == null ? "" : name;
		}

		@Override
		public String toString() {
			String n = name.isEmpty() ? text : name + " — " + text;
			if (file == null) {
				return "line " + line + ": " + n;
			}
			return file.getProjectRelativePath() + ":" + line + "  " + n;
		}
	}

	public static IRegion wordRegionAt(ShayaEditor editor, IDocument doc) {
		if (doc == null || editor == null) {
			return null;
		}
		try {
			int offset = 0;
			if (editor.getSelectionProvider().getSelection() instanceof ITextSelection) {
				ITextSelection sel = (ITextSelection) editor.getSelectionProvider().getSelection();
				if (sel.getLength() > 0) {
					return new Region(sel.getOffset(), sel.getLength());
				}
				offset = sel.getOffset();
			}
			return wordRegionAtOffset(doc, offset);
		} catch (Exception e) {
			return null;
		}
	}

	public static IRegion wordRegionAtOffset(IDocument doc, int offset) {
		try {
			int start = offset;
			while (start > 0 && ShayaIdentifiers.isIdentPart(doc.getChar(start - 1))) {
				start--;
			}
			int end = offset;
			while (end < doc.getLength() && ShayaIdentifiers.isIdentPart(doc.getChar(end))) {
				end++;
			}
			if (end <= start) {
				return null;
			}
			return new Region(start, end - start);
		} catch (BadLocationException e) {
			return null;
		}
	}

	public static List<Hit> findDeclarations(IDocument doc, IFile file, String word, boolean project) {
		List<Hit> hits = new ArrayList<>();
		if (word == null || word.isEmpty()) {
			return hits;
		}
		try {
			String engine = file != null ? ShayaToolchain.engineIdForName(file.getName()) : null;
			ShayaCommentStyle style = ShayaCommentStyle.forDialect(
					file != null ? ShayaKeywords.dialectOfFileName(file.getName()) : ShayaKeywords.Dialect.GENERIC);
			collectFromDocument(doc, file, word, style, hits);
			if (project && file != null && file.getProject() != null && engine != null) {
				scanProject(file.getProject(), word, file, engine, hits);
			}
		} catch (Exception ignored) {
		}
		return hits;
	}

	public static void openHit(ShayaEditor editor, Hit h) {
		if (editor == null || h == null) {
			return;
		}
		try {
			if (h.file == null || (editor.getEditorInput() instanceof FileEditorInput
					&& h.file.equals(((FileEditorInput) editor.getEditorInput()).getFile()))) {
				if (h.offset >= 0) {
					editor.selectAndReveal(h.offset, Math.max(1, h.length));
					return;
				}
			}
			if (h.file == null) {
				return;
			}
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

	private static void collectFromDocument(IDocument doc, IFile file, String word, ShayaCommentStyle style,
			List<Hit> hits) throws BadLocationException {
		if (doc == null) {
			return;
		}
		String text = doc.get();
		boolean[] mask = ShayaLexicalMask.mask(text, style);
		String w = word.toLowerCase(Locale.ROOT);
		int lines = doc.getNumberOfLines();
		for (int i = 0; i < lines; i++) {
			int off = doc.getLineOffset(i);
			int len = doc.getLineLength(i);
			int probe = off;
			while (probe < off + len && probe < mask.length
					&& (text.charAt(probe) == ' ' || text.charAt(probe) == '\t')) {
				probe++;
			}
			if (probe < mask.length && ShayaLexicalMask.covered(mask, probe)) {
				continue;
			}
			String line = doc.get(off, len).replace("\r", "").replace("\n", "");
			String trimmed = line.trim();
			if (trimmed.isEmpty()) {
				continue;
			}
			for (Pattern p : DEF_PATTERNS) {
				Matcher m = p.matcher(line);
				if (m.find() && w.equals(m.group(1).toLowerCase(Locale.ROOT))) {
					hits.add(new Hit(file, i + 1, off, Math.min(len, 60), trimmed, m.group(1)));
					break;
				}
			}
		}
	}

	private static void scanProject(IContainer root, String word, IFile skip, String engineId, List<Hit> hits)
			throws CoreException {
		root.accept(new IResourceProxyVisitor() {
			@Override
			public boolean visit(IResourceProxy proxy) throws CoreException {
				if (proxy.getType() != IResource.FILE || !ShayaToolchain.isShayaSource(proxy.getName())) {
					return true;
				}
				if (!engineId.equals(ShayaToolchain.engineIdForName(proxy.getName()))) {
					return true;
				}
				IResource r = proxy.requestResource();
				if (!(r instanceof IFile) || r.equals(skip)) {
					return true;
				}
				IFile f = (IFile) r;
				try {
					String text = new String(f.getContents(true).readAllBytes(), StandardCharsets.UTF_8);
					ShayaCommentStyle style = ShayaCommentStyle.forDialect(ShayaKeywords.dialectOfFileName(f.getName()));
					boolean[] mask = ShayaLexicalMask.mask(text, style);
					String[] lines = text.split("\\R", -1);
					String w = word.toLowerCase(Locale.ROOT);
					int offset = 0;
					for (int i = 0; i < lines.length; i++) {
						String line = lines[i];
						int probe = 0;
						while (probe < line.length()
								&& (line.charAt(probe) == ' ' || line.charAt(probe) == '\t')) {
							probe++;
						}
						if (offset + probe < mask.length && ShayaLexicalMask.covered(mask, offset + probe)) {
							offset += line.length() + 1;
							continue;
						}
						String trimmed = line.trim();
						if (!trimmed.isEmpty()) {
							for (Pattern p : DEF_PATTERNS) {
								Matcher m = p.matcher(line);
								if (m.find() && w.equals(m.group(1).toLowerCase(Locale.ROOT))) {
									hits.add(new Hit(f, i + 1, -1, 0, trimmed, m.group(1)));
									break;
								}
							}
						}
						offset += line.length() + 1;
					}
				} catch (Exception ignored) {
				}
				return true;
			}
		}, IResource.NONE);
	}
}
