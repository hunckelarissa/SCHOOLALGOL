package org.myau.shaya.ide.outline;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.viewers.ISelectionChangedListener;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.viewers.SelectionChangedEvent;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.views.contentoutline.ContentOutlinePage;
import org.myau.shaya.ide.editor.ShayaCommentStyle;
import org.myau.shaya.ide.editor.ShayaEditor;
import org.myau.shaya.ide.editor.ShayaLexicalMask;

/** Outline: алг / модуль with nested проц / функ; dialect-aware comment skip. */
public class ShayaContentOutlinePage extends ContentOutlinePage {

	private final ShayaEditor editor;
	private TreeViewer viewer;

	public ShayaContentOutlinePage(ShayaEditor editor) {
		this.editor = editor;
	}

	@Override
	public void createControl(Composite parent) {
		super.createControl(parent);
		viewer = getTreeViewer();
		viewer.setContentProvider(new OutlineContentProvider());
		viewer.setLabelProvider(new LabelProvider() {
			@Override
			public String getText(Object element) {
				if (element instanceof OutlineItem) {
					return ((OutlineItem) element).label;
				}
				return super.getText(element);
			}
		});
		viewer.addSelectionChangedListener(new ISelectionChangedListener() {
			@Override
			public void selectionChanged(SelectionChangedEvent event) {
				Object el = ((IStructuredSelection) event.getSelection()).getFirstElement();
				if (el instanceof OutlineItem) {
					OutlineItem item = (OutlineItem) el;
					editor.selectAndReveal(item.offset, item.length);
				}
			}
		});
		setInput(editor);
	}

	public void setInput(ShayaEditor ed) {
		if (viewer != null) {
			viewer.setInput(ed);
			viewer.expandAll();
		}
	}

	public void refresh() {
		if (viewer != null && !viewer.getControl().isDisposed()) {
			Object[] expanded = viewer.getExpandedElements();
			viewer.refresh();
			viewer.setExpandedElements(expanded);
			if (expanded.length == 0) {
				viewer.expandAll();
			}
		}
	}

	public static final class OutlineItem {
		public final String label;
		public final int offset;
		public final int length;
		public final List<OutlineItem> children = new ArrayList<>();

		OutlineItem(String label, int offset, int length) {
			this.label = label;
			this.offset = offset;
			this.length = length;
		}

		@Override
		public String toString() {
			return label;
		}
	}

	/** Symbols for Outline view / Quick Outline (Ctrl+O) — flattened with indent. */
	public static List<OutlineItem> listSymbols(IDocument doc) {
		return listSymbols(doc, ShayaCommentStyle.LINE_SLASH);
	}

	public static List<OutlineItem> listSymbols(IDocument doc, ShayaCommentStyle style) {
		if (doc == null) {
			return List.of();
		}
		List<OutlineItem> roots = OutlineContentProvider.parse(doc, style);
		List<OutlineItem> flat = new ArrayList<>();
		for (OutlineItem r : roots) {
			flat.add(r);
			for (OutlineItem c : r.children) {
				flat.add(new OutlineItem("  " + c.label, c.offset, c.length));
			}
		}
		return flat;
	}

	private static final class OutlineContentProvider implements ITreeContentProvider {
		@Override
		public Object[] getElements(Object inputElement) {
			if (!(inputElement instanceof ShayaEditor)) {
				return new Object[0];
			}
			ShayaEditor ed = (ShayaEditor) inputElement;
			IDocument doc = ed.getEditorDocument();
			if (doc == null) {
				return new Object[0];
			}
			ShayaCommentStyle style = ShayaCommentStyle.forDialect(ed.currentDialect());
			return parse(doc, style).toArray();
		}

		static List<OutlineItem> parse(IDocument doc, ShayaCommentStyle style) {
			List<OutlineItem> roots = new ArrayList<>();
			OutlineItem currentParent = null;
			boolean sawAlg = false;
			String text;
			try {
				text = doc.get();
			} catch (Exception e) {
				return roots;
			}
			boolean[] mask = ShayaLexicalMask.mask(text, style != null ? style : ShayaCommentStyle.LINE_SLASH);
			try {
				int lines = doc.getNumberOfLines();
				for (int line = 0; line < lines; line++) {
					int off = doc.getLineOffset(line);
					int len = doc.getLineLength(line);
					if (off < mask.length && ShayaLexicalMask.covered(mask, off)) {
						// skip if line offset is inside comment (e.g. mid block (* *))
						int probe = off;
						while (probe < off + len && probe < mask.length
								&& (text.charAt(probe) == ' ' || text.charAt(probe) == '\t')) {
							probe++;
						}
						if (probe < mask.length && ShayaLexicalMask.covered(mask, probe)) {
							continue;
						}
					}
					String lineText = doc.get(off, len).replace("\r", "").replace("\n", "").trim();
					if (lineText.isEmpty()) {
						continue;
					}
					String lower = lineText.toLowerCase(Locale.ROOT);
					OutlineItem item = match(lower, lineText, off, len);
					if (item == null) {
						continue;
					}
					if (item.label.startsWith("алг") || item.label.startsWith("модуль")) {
						sawAlg = true;
						roots.add(item);
						currentParent = item;
					} else if (currentParent != null) {
						currentParent.children.add(item);
					} else {
						roots.add(item);
					}
				}
				if (!sawAlg) {
					for (int line = 0; line < lines; line++) {
						int off = doc.getLineOffset(line);
						int len = doc.getLineLength(line);
						int probe = off;
						while (probe < off + len && probe < mask.length
								&& (text.charAt(probe) == ' ' || text.charAt(probe) == '\t')) {
							probe++;
						}
						if (probe < mask.length && ShayaLexicalMask.covered(mask, probe)) {
							continue;
						}
						String lineText = doc.get(off, len).replace("\r", "").replace("\n", "").trim();
						String lower = lineText.toLowerCase(Locale.ROOT);
						if (lower.equals("нач") || lower.startsWith("нач ") || lower.startsWith("нач\t")) {
							roots.add(0, new OutlineItem("нач (тело)", off, Math.min(len, 80)));
							break;
						}
					}
				}
			} catch (BadLocationException ignored) {
			}
			return roots;
		}

		private static OutlineItem match(String lower, String text, int off, int len) {
			if (lower.startsWith("алг ") || lower.equals("алг") || lower.startsWith("алг\t")) {
				return named("алг", text, off, len);
			}
			if (lower.startsWith("проц ") || lower.startsWith("проц\t")) {
				return named("проц", text, off, len);
			}
			if (lower.startsWith("функ ") || lower.startsWith("функ\t")) {
				return named("функ", text, off, len);
			}
			if (lower.startsWith("модуль ") || lower.startsWith("модуль\t")) {
				return named("модуль", text, off, len);
			}
			return null;
		}

		private static OutlineItem named(String kind, String text, int off, int len) {
			String[] parts = text.split("[\\s(;]+");
			String name = parts.length >= 2 ? parts[1] : "?";
			return new OutlineItem(kind + " " + name, off, Math.min(len, 80));
		}

		@Override
		public Object[] getChildren(Object parentElement) {
			if (parentElement instanceof OutlineItem) {
				return ((OutlineItem) parentElement).children.toArray();
			}
			return new Object[0];
		}

		@Override
		public Object getParent(Object element) {
			return null;
		}

		@Override
		public boolean hasChildren(Object element) {
			return element instanceof OutlineItem && !((OutlineItem) element).children.isEmpty();
		}

		@Override
		public void dispose() {
		}

		@Override
		public void inputChanged(Viewer viewer, Object oldInput, Object newInput) {
		}
	}
}
