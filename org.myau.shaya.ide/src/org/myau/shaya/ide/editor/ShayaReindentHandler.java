package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.handlers.HandlerUtil;

/** Reindent the whole buffer by нач/если/нц… ↔ кон/все/кц nesting (prefs indent). */
public class ShayaReindentHandler extends AbstractHandler {

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
		try {
			int lines = doc.getNumberOfLines();
			List<String> out = new ArrayList<>(lines);
			int depth = 0;
			for (int i = 0; i < lines; i++) {
				IRegion reg = doc.getLineInformation(i);
				String raw = doc.get(reg.getOffset(), reg.getLength());
				String trimmed = raw.trim();
				int lineDepth = depth;
				if (!trimmed.isEmpty() && !ShayaIndent.isComment(trimmed)) {
					String kw = ShayaIndent.leadingKeyword(trimmed);
					if (ShayaIndent.isCloserOrMid(kw)) {
						lineDepth = Math.max(0, depth - 1);
					}
				}
				if (trimmed.isEmpty()) {
					out.add("");
				} else {
					out.add(ShayaIndent.repeat(ShayaIndent.unit(), lineDepth) + trimmed);
				}
				if (!trimmed.isEmpty() && !ShayaIndent.isComment(trimmed)) {
					depth = adjustDepth(depth, trimmed);
				}
			}
			String nl = doc.getLegalLineDelimiters()[0];
			StringBuilder sb = new StringBuilder();
			for (int i = 0; i < out.size(); i++) {
				if (i > 0) {
					sb.append(nl);
				}
				sb.append(out.get(i));
			}
			doc.set(sb.toString());
		} catch (BadLocationException ignored) {
		}
		return null;
	}

	private static int adjustDepth(int depth, String trimmed) {
		String lower = trimmed.toLowerCase(Locale.ROOT);
		String kw = ShayaIndent.leadingKeyword(trimmed);
		if (ShayaIndent.isCloser(kw)) {
			return Math.max(0, depth - 1);
		}
		if ("иначе".equals(kw) || "инес".equals(kw) || "иначе_если".equals(kw)) {
			return depth;
		}
		if (ShayaIndent.isOpener(kw)) {
			if (containsKeyword(lower, "кон") || containsKeyword(lower, "все")
					|| containsKeyword(lower, "кц") || containsKeyword(lower, "кесли")) {
				return depth;
			}
			return depth + 1;
		}
		return depth;
	}

	private static boolean containsKeyword(String lower, String kw) {
		int idx = lower.indexOf(kw);
		while (idx >= 0) {
			boolean leftOk = idx == 0 || !ShayaIdentifiers.isIdentPart(lower.charAt(idx - 1));
			int end = idx + kw.length();
			boolean rightOk = end >= lower.length() || !ShayaIdentifiers.isIdentPart(lower.charAt(end));
			if (leftOk && rightOk) {
				return true;
			}
			idx = lower.indexOf(kw, idx + 1);
		}
		return false;
	}
}
