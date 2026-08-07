package org.myau.shaya.ide.editor;

import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.Region;
import org.eclipse.jface.text.source.DefaultCharacterPairMatcher;
import org.eclipse.jface.text.source.ICharacterPairMatcher;

/**
 * Bracket matcher plus keyword pair paint (нач↔кон, если↔все, …) via {@link ShayaBlockMatcher}.
 */
public final class ShayaKeywordPairMatcher implements ICharacterPairMatcher {

	private final DefaultCharacterPairMatcher brackets = new DefaultCharacterPairMatcher(
			new char[] { '(', ')', '[', ']', '{', '}' });
	private final ShayaEditor editor;
	private int anchor = ICharacterPairMatcher.LEFT;

	public ShayaKeywordPairMatcher(ShayaEditor editor) {
		this.editor = editor;
	}

	@Override
	public IRegion match(IDocument document, int offset) {
		IRegion br = brackets.match(document, offset);
		if (br != null) {
			anchor = brackets.getAnchor();
			return br;
		}
		if (document == null || offset < 0) {
			return null;
		}
		try {
			ShayaCommentStyle style = ShayaCommentStyle.forDialect(
					editor != null ? editor.currentDialect() : ShayaKeywords.Dialect.GENERIC);
			int probe = offset > 0 ? offset - 1 : offset;
			int match = ShayaBlockMatcher.findMatch(document, Math.max(0, probe), style);
			if (match < 0 && offset < document.getLength()) {
				match = ShayaBlockMatcher.findMatch(document, offset, style);
				probe = offset;
			}
			if (match < 0) {
				return null;
			}
			IRegion here = ShayaDeclarations.wordRegionAtOffset(document, Math.max(0, probe));
			IRegion there = ShayaDeclarations.wordRegionAtOffset(document, match);
			if (here == null || there == null) {
				return null;
			}
			int a = Math.min(here.getOffset(), there.getOffset());
			int b = Math.max(here.getOffset() + here.getLength(), there.getOffset() + there.getLength());
			anchor = here.getOffset() <= there.getOffset() ? ICharacterPairMatcher.LEFT
					: ICharacterPairMatcher.RIGHT;
			return new Region(a, b - a);
		} catch (Exception e) {
			return null;
		}
	}

	@Override
	public void clear() {
		brackets.clear();
	}

	@Override
	public void dispose() {
		brackets.dispose();
	}

	@Override
	public int getAnchor() {
		return anchor;
	}
}
