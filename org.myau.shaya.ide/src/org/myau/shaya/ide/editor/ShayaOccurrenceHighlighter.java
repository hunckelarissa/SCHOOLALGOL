package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.DocumentEvent;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IDocumentListener;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.Position;
import org.eclipse.jface.text.source.Annotation;
import org.eclipse.jface.text.source.IAnnotationModel;
import org.eclipse.jface.text.source.IAnnotationModelExtension;
import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.jface.viewers.ISelectionChangedListener;
import org.eclipse.jface.viewers.SelectionChangedEvent;
import org.eclipse.swt.widgets.Display;

/** Highlights all occurrences of the identifier under the caret. */
public final class ShayaOccurrenceHighlighter
		implements ISelectionChangedListener, IDocumentListener {

	public static final String TYPE = "org.myau.shaya.ide.occurrence";

	private final ShayaEditor editor;
	private String lastWord = "";
	private int lastOffset = -1;
	private Runnable pending;

	public ShayaOccurrenceHighlighter(ShayaEditor editor) {
		this.editor = editor;
	}

	public void install() {
		ISourceViewer viewer = editor.getSourceViewerPublic();
		if (viewer == null) {
			return;
		}
		viewer.getSelectionProvider().addSelectionChangedListener(this);
		IDocument doc = editor.getEditorDocument();
		if (doc != null) {
			doc.addDocumentListener(this);
		}
	}

	public void uninstall() {
		ISourceViewer viewer = editor.getSourceViewerPublic();
		if (viewer != null) {
			viewer.getSelectionProvider().removeSelectionChangedListener(this);
		}
		IDocument doc = editor.getEditorDocument();
		if (doc != null) {
			doc.removeDocumentListener(this);
		}
		clear();
	}

	@Override
	public void selectionChanged(SelectionChangedEvent event) {
		schedule();
	}

	@Override
	public void documentAboutToBeChanged(DocumentEvent event) {
		/* ignore */
	}

	@Override
	public void documentChanged(DocumentEvent event) {
		schedule();
	}

	private void schedule() {
		if (pending != null) {
			Display.getDefault().timerExec(-1, pending);
		}
		pending = () -> {
			pending = null;
			update();
		};
		Display.getDefault().timerExec(250, pending);
	}

	private void update() {
		ISourceViewer viewer = editor.getSourceViewerPublic();
		IDocument doc = editor.getEditorDocument();
		if (viewer == null || doc == null) {
			return;
		}
		ITextSelection sel = null;
		if (viewer.getSelectionProvider().getSelection() instanceof ITextSelection) {
			sel = (ITextSelection) viewer.getSelectionProvider().getSelection();
		}
		if (sel == null) {
			clear();
			return;
		}
		int offset = sel.getOffset();
		String word = wordAt(doc, offset);
		if (word == null || word.length() < 2 || isKeywordNoise(word)) {
			clear();
			lastWord = "";
			lastOffset = offset;
			return;
		}
		if (word.equals(lastWord) && Math.abs(offset - lastOffset) < 2) {
			return;
		}
		lastWord = word;
		lastOffset = offset;
		List<Position> hits = findAll(doc, word);
		IAnnotationModel model = viewer.getAnnotationModel();
		if (model == null) {
			return;
		}
		Map<Annotation, Position> add = new HashMap<>();
		for (Position p : hits) {
			add.put(new Annotation(TYPE, false, word), p);
		}
		Annotation[] remove = collectOurs(model);
		if (model instanceof IAnnotationModelExtension) {
			((IAnnotationModelExtension) model).replaceAnnotations(remove, add);
		} else {
			for (Annotation a : remove) {
				model.removeAnnotation(a);
			}
			for (Map.Entry<Annotation, Position> e : add.entrySet()) {
				model.addAnnotation(e.getKey(), e.getValue());
			}
		}
	}

	private void clear() {
		ISourceViewer viewer = editor.getSourceViewerPublic();
		if (viewer == null) {
			return;
		}
		IAnnotationModel model = viewer.getAnnotationModel();
		if (model == null) {
			return;
		}
		Annotation[] remove = collectOurs(model);
		if (remove.length == 0) {
			return;
		}
		if (model instanceof IAnnotationModelExtension) {
			((IAnnotationModelExtension) model).replaceAnnotations(remove, null);
		} else {
			for (Annotation a : remove) {
				model.removeAnnotation(a);
			}
		}
	}

	private static Annotation[] collectOurs(IAnnotationModel model) {
		List<Annotation> list = new ArrayList<>();
		Iterator<?> it = model.getAnnotationIterator();
		while (it.hasNext()) {
			Object next = it.next();
			if (next instanceof Annotation) {
				Annotation a = (Annotation) next;
				if (TYPE.equals(a.getType())) {
					list.add(a);
				}
			}
		}
		return list.toArray(new Annotation[0]);
	}

	private static String wordAt(IDocument doc, int offset) {
		try {
			int start = offset;
			while (start > 0) {
				char c = doc.getChar(start - 1);
				if (!isIdent(c)) {
					break;
				}
				start--;
			}
			int end = offset;
			int len = doc.getLength();
			while (end < len) {
				char c = doc.getChar(end);
				if (!isIdent(c)) {
					break;
				}
				end++;
			}
			if (end <= start) {
				return null;
			}
			return doc.get(start, end - start);
		} catch (BadLocationException e) {
			return null;
		}
	}

	private List<Position> findAll(IDocument doc, String word) {
		List<Position> out = new ArrayList<>();
		String text = doc.get();
		boolean[] mask = ShayaLexicalMask.mask(text, ShayaCommentStyle.forDialect(editor.currentDialect()));
		String lower = text.toLowerCase(Locale.ROOT);
		String needle = word.toLowerCase(Locale.ROOT);
		int from = 0;
		while (from < lower.length()) {
			int at = lower.indexOf(needle, from);
			if (at < 0) {
				break;
			}
			if (isIdentBoundary(text, at, needle.length()) && !ShayaLexicalMask.covered(mask, at)) {
				out.add(new Position(at, word.length()));
			}
			from = at + needle.length();
			if (out.size() > 200) {
				break;
			}
		}
		return out;
	}

	private static boolean isIdentBoundary(String text, int at, int len) {
		if (at > 0 && isIdent(text.charAt(at - 1))) {
			return false;
		}
		int end = at + len;
		if (end < text.length() && isIdent(text.charAt(end))) {
			return false;
		}
		return true;
	}

	private static boolean isIdent(char c) {
		return Character.isLetterOrDigit(c) || c == '_';
	}

	private boolean isKeywordNoise(String word) {
		return ShayaKeywords.isKeyword(word, editor.currentDialect());
	}
}
