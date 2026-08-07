package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.List;

import org.eclipse.jface.text.TextAttribute;
import org.eclipse.jface.text.rules.IRule;
import org.eclipse.jface.text.rules.IToken;
import org.eclipse.jface.text.rules.IWordDetector;
import org.eclipse.jface.text.rules.MultiLineRule;
import org.eclipse.jface.text.rules.NumberRule;
import org.eclipse.jface.text.rules.RuleBasedScanner;
import org.eclipse.jface.text.rules.SingleLineRule;
import org.eclipse.jface.text.rules.Token;
import org.eclipse.jface.text.rules.WhitespaceRule;
import org.eclipse.jface.text.rules.WordRule;
import org.eclipse.swt.SWT;

/** Token scanner for ALG sources — keywords + comment style per dialect. */
public class ShayaCodeScanner extends RuleBasedScanner {

	public ShayaCodeScanner(ShayaColorManager colors, ShayaKeywords.Dialect dialect) {
		IToken keyword = new Token(new TextAttribute(colors.getColor(ShayaColors.KEYWORD), null, SWT.BOLD));
		IToken type = new Token(new TextAttribute(colors.getColor(ShayaColors.TYPE), null, SWT.BOLD));
		IToken builtin = new Token(new TextAttribute(colors.getColor(ShayaColors.BUILTIN)));
		IToken string = new Token(new TextAttribute(colors.getColor(ShayaColors.STRING)));
		IToken comment = new Token(new TextAttribute(colors.getColor(ShayaColors.COMMENT), null, SWT.ITALIC));
		IToken number = new Token(new TextAttribute(colors.getColor(ShayaColors.NUMBER)));
		IToken other = new Token(new TextAttribute(colors.getColor(ShayaColors.DEFAULT)));

		WordRule wordRule = new WordRule(new IdentDetector(), other, true);
		addWords(wordRule, ShayaKeywords.controlFor(dialect), keyword);
		addWords(wordRule, ShayaKeywords.typesFor(dialect), type);
		addWords(wordRule, ShayaKeywords.builtinsFor(dialect), builtin);

		List<IRule> rules = new ArrayList<>();
		ShayaCommentStyle style = ShayaCommentStyle.forDialect(dialect);
		switch (style) {
		case LINE_PIPE:
			rules.add(new SingleLineRule("|", "", comment));
			break;
		case BLOCK_PAREN:
			rules.add(new MultiLineRule("(*", "*)", comment));
			break;
		case LINE_SLASH:
		default:
			rules.add(new MultiLineRule("/*", "*/", comment));
			rules.add(new SingleLineRule("//", "", comment));
			rules.add(new SingleLineRule("#", "", comment));
			break;
		}
		rules.add(new SingleLineRule("\"", "\"", string, '\\'));
		rules.add(new SingleLineRule("'", "'", string, '\\'));
		rules.add(new WhitespaceRule(c -> Character.isWhitespace(c)));
		rules.add(wordRule);
		rules.add(new NumberRule(number));
		setRules(rules.toArray(new IRule[0]));
	}

	private static void addWords(WordRule rule, String[] words, IToken token) {
		for (String w : words) {
			rule.addWord(w, token);
			rule.addWord(w.toUpperCase(), token);
		}
	}

	public static class IdentDetector implements IWordDetector {
		@Override
		public boolean isWordStart(char c) {
			return Character.isLetter(c) || c == '_';
		}

		@Override
		public boolean isWordPart(char c) {
			return Character.isLetterOrDigit(c) || c == '_';
		}
	}
}
