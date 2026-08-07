package org.myau.shaya.ide.editor;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.DocumentCommand;
import org.eclipse.jface.text.IAutoEditStrategy;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;

/** Enter auto-indent: copy previous indent; deepen after нач/если/нц… */
public class ShayaAutoIndentStrategy implements IAutoEditStrategy {

	@Override
	public void customizeDocumentCommand(IDocument document, DocumentCommand command) {
		if (command == null || document == null || command.length != 0 || command.text == null) {
			return;
		}
		if (!isLineDelimiter(document, command.text)) {
			return;
		}
		try {
			int line = document.getLineOfOffset(command.offset);
			IRegion info = document.getLineInformation(line);
			String raw = document.get(info.getOffset(), info.getLength());
			String indent = ShayaIndent.leadingWhitespace(raw);
			String trimmed = raw.trim();
			if (ShayaIndent.opensBlock(trimmed)) {
				indent = indent + ShayaIndent.unit();
			} else if (!trimmed.isEmpty() && !ShayaIndent.isComment(trimmed)
					&& ShayaIndent.isCloserOrMid(ShayaIndent.leadingKeyword(trimmed))) {
				// closer on this line: next line stays at same indent as this line's visual
			}
			command.text = command.text + indent;
		} catch (BadLocationException ignored) {
		}
	}

	private static boolean isLineDelimiter(IDocument doc, String text) {
		String[] delims = doc.getLegalLineDelimiters();
		for (String d : delims) {
			if (d.equals(text)) {
				return true;
			}
		}
		return false;
	}
}
