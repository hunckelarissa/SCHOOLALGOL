package org.myau.shaya.ide.editor;

import java.util.Arrays;
import java.util.Comparator;
import java.util.Locale;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.TextSelection;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.handlers.HandlerUtil;

/** Line edits: duplicate / move / join / sort. */
public class ShayaLineEditHandler extends AbstractHandler {

	public static final String DUPLICATE = "org.myau.shaya.ide.commands.duplicateLine";
	public static final String MOVE_UP = "org.myau.shaya.ide.commands.moveLineUp";
	public static final String MOVE_DOWN = "org.myau.shaya.ide.commands.moveLineDown";
	public static final String JOIN = "org.myau.shaya.ide.commands.joinLines";
	public static final String SORT = "org.myau.shaya.ide.commands.sortLines";

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		IEditorPart part = HandlerUtil.getActiveEditor(event);
		if (!(part instanceof ShayaEditor)) {
			return null;
		}
		ShayaEditor editor = (ShayaEditor) part;
		IDocument doc = editor.getEditorDocument();
		if (doc == null) {
			return null;
		}
		String cmd = event.getCommand() != null ? event.getCommand().getId() : "";
		try {
			if (DUPLICATE.equals(cmd)) {
				duplicate(editor, doc);
			} else if (MOVE_UP.equals(cmd)) {
				move(editor, doc, -1);
			} else if (MOVE_DOWN.equals(cmd)) {
				move(editor, doc, +1);
			} else if (JOIN.equals(cmd)) {
				join(editor, doc);
			} else if (SORT.equals(cmd)) {
				sort(editor, doc);
			}
		} catch (BadLocationException ignored) {
		}
		return null;
	}

	private static void duplicate(ShayaEditor editor, IDocument doc) throws BadLocationException {
		ITextSelection sel = selection(editor);
		int startLine = sel.getStartLine();
		int endLine = sel.getEndLine();
		int startOff = doc.getLineOffset(startLine);
		IRegion endInfo = doc.getLineInformation(endLine);
		int endOff = endInfo.getOffset() + endInfo.getLength();
		String delim = doc.getLineDelimiter(endLine);
		if (delim != null) {
			endOff += delim.length();
		}
		String block = doc.get(startOff, endOff - startOff);
		if (delim == null && endLine == doc.getNumberOfLines() - 1) {
			block = block + doc.getLegalLineDelimiters()[0];
		}
		doc.replace(endOff, 0, block);
		editor.getSelectionProvider().setSelection(new TextSelection(endOff, Math.max(0, block.length() - 1)));
	}

	/** Swap selected lines with the neighbour; keep per-line delimiters and EOF newline. */
	private static void move(ShayaEditor editor, IDocument doc, int dir) throws BadLocationException {
		ITextSelection sel = selection(editor);
		int startLine = sel.getStartLine();
		int endLine = sel.getEndLine();
		int lineCount = doc.getNumberOfLines();
		if (dir < 0 && startLine <= 0) {
			return;
		}
		if (dir > 0 && endLine >= lineCount - 1) {
			return;
		}

		int from = dir < 0 ? startLine - 1 : startLine;
		int to = dir < 0 ? endLine : endLine + 1;
		int n = to - from + 1;
		String[] texts = new String[n];
		String[] delims = new String[n];
		for (int i = 0; i < n; i++) {
			int line = from + i;
			IRegion info = doc.getLineInformation(line);
			texts[i] = doc.get(info.getOffset(), info.getLength());
			delims[i] = doc.getLineDelimiter(line);
		}

		if (dir < 0) {
			String first = texts[0];
			for (int i = 0; i < n - 1; i++) {
				texts[i] = texts[i + 1];
			}
			texts[n - 1] = first;
		} else {
			String last = texts[n - 1];
			for (int i = n - 1; i > 0; i--) {
				texts[i] = texts[i - 1];
			}
			texts[0] = last;
		}

		int startOff = doc.getLineOffset(from);
		IRegion toInfo = doc.getLineInformation(to);
		int endOff = toInfo.getOffset() + toInfo.getLength();
		boolean hadFinalDelim = delims[n - 1] != null;
		if (hadFinalDelim) {
			endOff += delims[n - 1].length();
		}

		String fallbackNl = doc.getLegalLineDelimiters()[0];
		StringBuilder sb = new StringBuilder();
		for (int i = 0; i < n; i++) {
			sb.append(texts[i]);
			if (i < n - 1) {
				sb.append(delims[i] != null ? delims[i] : fallbackNl);
			} else if (hadFinalDelim) {
				sb.append(delims[n - 1] != null ? delims[n - 1] : fallbackNl);
			}
		}
		doc.replace(startOff, endOff - startOff, sb.toString());

		int newStart = dir < 0 ? startLine - 1 : startLine + 1;
		selectLines(editor, doc, newStart, endLine - startLine);
	}

	private static void selectLines(ShayaEditor editor, IDocument doc, int startLine, int extraLines)
			throws BadLocationException {
		int startOff = doc.getLineOffset(startLine);
		int endLine = startLine + extraLines;
		IRegion endInfo = doc.getLineInformation(endLine);
		int len = endInfo.getOffset() + endInfo.getLength() - startOff;
		editor.getSelectionProvider().setSelection(new TextSelection(startOff, Math.max(0, len)));
	}

	private static void join(ShayaEditor editor, IDocument doc) throws BadLocationException {
		ITextSelection sel = selection(editor);
		int startLine = sel.getStartLine();
		int endLine = sel.getEndLine();
		if (sel.getLength() == 0 || startLine == endLine) {
			endLine = Math.min(doc.getNumberOfLines() - 1, startLine + 1);
		}
		if (endLine <= startLine) {
			return;
		}
		StringBuilder joined = new StringBuilder();
		for (int i = startLine; i <= endLine; i++) {
			IRegion info = doc.getLineInformation(i);
			String line = doc.get(info.getOffset(), info.getLength()).trim();
			if (line.isEmpty()) {
				continue;
			}
			if (joined.length() > 0) {
				joined.append(' ');
			}
			joined.append(line);
		}
		int startOff = doc.getLineOffset(startLine);
		IRegion endInfo = doc.getLineInformation(endLine);
		int endOff = endInfo.getOffset() + endInfo.getLength();
		String delim = doc.getLineDelimiter(endLine);
		if (delim != null) {
			endOff += delim.length();
		}
		String nl = delim != null ? delim : doc.getLegalLineDelimiters()[0];
		doc.replace(startOff, endOff - startOff, joined.toString() + nl);
		editor.getSelectionProvider().setSelection(new TextSelection(startOff, joined.length()));
	}

	private static void sort(ShayaEditor editor, IDocument doc) throws BadLocationException {
		ITextSelection sel = selection(editor);
		int startLine = sel.getStartLine();
		int endLine = sel.getEndLine();
		if (endLine <= startLine) {
			return;
		}
		int n = endLine - startLine + 1;
		String[] lines = new String[n];
		String[] delims = new String[n];
		for (int i = 0; i < n; i++) {
			IRegion info = doc.getLineInformation(startLine + i);
			lines[i] = doc.get(info.getOffset(), info.getLength());
			delims[i] = doc.getLineDelimiter(startLine + i);
		}
		Arrays.sort(lines, Comparator.comparing(s -> s.toUpperCase(Locale.ROOT)));
		String fallbackNl = doc.getLegalLineDelimiters()[0];
		boolean hadFinalDelim = delims[n - 1] != null;
		StringBuilder sb = new StringBuilder();
		for (int i = 0; i < n; i++) {
			if (i > 0) {
				sb.append(delims[i - 1] != null ? delims[i - 1] : fallbackNl);
			}
			sb.append(lines[i]);
		}
		int startOff = doc.getLineOffset(startLine);
		IRegion endInfo = doc.getLineInformation(endLine);
		int endOff = endInfo.getOffset() + endInfo.getLength();
		if (hadFinalDelim) {
			endOff += delims[n - 1].length();
			sb.append(delims[n - 1]);
		}
		doc.replace(startOff, endOff - startOff, sb.toString());
		selectLines(editor, doc, startLine, endLine - startLine);
	}

	private static ITextSelection selection(ShayaEditor editor) {
		if (editor.getSelectionProvider().getSelection() instanceof ITextSelection) {
			return (ITextSelection) editor.getSelectionProvider().getSelection();
		}
		return new TextSelection(0, 0);
	}
}
