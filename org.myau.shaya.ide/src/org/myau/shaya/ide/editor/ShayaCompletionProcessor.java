package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.ITextViewer;
import org.eclipse.jface.text.contentassist.CompletionProposal;
import org.eclipse.jface.text.contentassist.ICompletionProposal;
import org.eclipse.jface.text.contentassist.IContentAssistProcessor;
import org.eclipse.jface.text.contentassist.IContextInformation;
import org.eclipse.jface.text.contentassist.IContextInformationValidator;

/** Ctrl+Space / auto-activation: templates + keywords (extension → dialect). */
public class ShayaCompletionProcessor implements IContentAssistProcessor {

	private final ShayaEditor editor;

	public ShayaCompletionProcessor(ShayaEditor editor) {
		this.editor = editor;
	}

	@Override
	public ICompletionProposal[] computeCompletionProposals(ITextViewer viewer, int offset) {
		IDocument doc = viewer.getDocument();
		if (doc == null) {
			return new ICompletionProposal[0];
		}
		ShayaKeywords.Dialect dialect = editor != null ? editor.currentDialect() : ShayaKeywords.Dialect.GENERIC;
		String prefix = prefixAt(doc, offset);
		String lower = prefix.toLowerCase(Locale.ROOT);
		int replaceStart = offset - prefix.length();
		String info = dialect.name();
		boolean lineStart = isLineStartContext(doc, offset, prefix);

		List<ICompletionProposal> templates = new ArrayList<>();
		List<ICompletionProposal> keywords = new ArrayList<>();
		Set<String> seenInsert = new LinkedHashSet<>();

		for (ShayaTemplates.Template t : ShayaTemplates.forDialect(dialect)) {
			String key = t.label.replace("…", "").toLowerCase(Locale.ROOT);
			if (lower.isEmpty() || key.startsWith(lower) || t.label.toLowerCase(Locale.ROOT).startsWith(lower)) {
				if (seenInsert.add(t.body)) {
					templates.add(new CompletionProposal(t.body, replaceStart, prefix.length(), t.cursor, null,
							t.label + "  — template", null, info));
				}
			}
		}
		for (String word : ShayaKeywords.proposalsFor(dialect)) {
			if (lower.isEmpty() || word.toLowerCase(Locale.ROOT).startsWith(lower)) {
				if (seenInsert.add(word)) {
					keywords.add(new CompletionProposal(word, replaceStart, prefix.length(), word.length(), null,
							word, null, info));
				}
			}
		}

		List<ICompletionProposal> list = new ArrayList<>(templates.size() + keywords.size());
		if (lineStart || prefix.isEmpty()) {
			list.addAll(templates);
			list.addAll(keywords);
		} else {
			list.addAll(keywords);
			list.addAll(templates);
		}
		return list.toArray(new ICompletionProposal[0]);
	}

	/** True when prefix starts at beginning of line (ignoring indent). */
	private static boolean isLineStartContext(IDocument doc, int offset, String prefix) {
		try {
			int line = doc.getLineOfOffset(offset);
			int lineOff = doc.getLineOffset(line);
			int i = lineOff;
			while (i < offset - prefix.length()) {
				char c = doc.getChar(i);
				if (c != ' ' && c != '\t') {
					return false;
				}
				i++;
			}
			return true;
		} catch (BadLocationException e) {
			return false;
		}
	}

	private static String prefixAt(IDocument doc, int offset) {
		try {
			int start = offset;
			while (start > 0) {
				char c = doc.getChar(start - 1);
				if (!Character.isLetterOrDigit(c) && c != '_') {
					break;
				}
				start--;
			}
			return doc.get(start, offset - start);
		} catch (BadLocationException e) {
			return "";
		}
	}

	@Override
	public IContextInformation[] computeContextInformation(ITextViewer viewer, int offset) {
		return new IContextInformation[0];
	}

	@Override
	public char[] getCompletionProposalAutoActivationCharacters() {
		return ("абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
				+ "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
				+ "abcdefghijklmnopqrstuvwxyz"
				+ "ABCDEFGHIJKLMNOPQRSTUVWXYZ_").toCharArray();
	}

	@Override
	public char[] getContextInformationAutoActivationCharacters() {
		return null;
	}

	@Override
	public String getErrorMessage() {
		return null;
	}

	@Override
	public IContextInformationValidator getContextInformationValidator() {
		return null;
	}
}
