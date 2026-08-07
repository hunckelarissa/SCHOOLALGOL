package org.myau.shaya.ide.editor;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.DocumentCommand;
import org.eclipse.jface.text.IAutoEditStrategy;
import org.eclipse.jface.text.IDocument;

/**
 * Smart typing: () [] "" and (* *) — skip if closer already present.
 */
public class ShayaSmartTypingStrategy implements IAutoEditStrategy {

	@Override
	public void customizeDocumentCommand(IDocument document, DocumentCommand command) {
		if (command == null || document == null || command.length != 0 || command.text == null
				|| command.text.length() != 1) {
			return;
		}
		char c = command.text.charAt(0);
		try {
			if (c == '(') {
				pair(document, command, ')');
			} else if (c == '[') {
				pair(document, command, ']');
			} else if (c == '"') {
				pair(document, command, '"');
			} else if (c == '*') {
				// (* *) after auto-paired (): typing * between (|) replaces ) with *)
				if (command.offset > 0 && document.getChar(command.offset - 1) == '(') {
					if (nextIs(document, command.offset, ')')) {
						command.text = "*)";
						command.length = 1;
						command.caretOffset = command.offset + 1;
						command.shiftsCaret = false;
					} else if (!nextIs(document, command.offset, '*')) {
						command.text = "*)";
						command.caretOffset = command.offset + 1;
						command.shiftsCaret = false;
					}
				}
			} else if (c == ')' || c == ']' || c == '"') {
				// type-over matching closer
				if (nextIs(document, command.offset, c)) {
					command.text = "";
					command.caretOffset = command.offset + 1;
					command.shiftsCaret = false;
				}
			}
		} catch (BadLocationException ignored) {
		}
	}

	private static void pair(IDocument document, DocumentCommand command, char close)
			throws BadLocationException {
		if (nextIs(document, command.offset, close)) {
			return;
		}
		command.text = command.text + close;
		command.caretOffset = command.offset + 1;
		command.shiftsCaret = false;
	}

	private static boolean nextIs(IDocument document, int offset, char expected)
			throws BadLocationException {
		return offset < document.getLength() && document.getChar(offset) == expected;
	}
}
