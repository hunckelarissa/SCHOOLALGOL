package org.myau.shaya.ide.editor;

import java.util.List;

import org.eclipse.core.resources.IFile;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextViewer;
import org.eclipse.jface.text.hyperlink.AbstractHyperlinkDetector;
import org.eclipse.jface.text.hyperlink.IHyperlink;
import org.eclipse.ui.part.FileEditorInput;

/** Ctrl+Click → Go to Declaration. */
public class ShayaHyperlinkDetector extends AbstractHyperlinkDetector {

	private final ShayaEditor editor;

	public ShayaHyperlinkDetector(ShayaEditor editor) {
		this.editor = editor;
	}

	@Override
	public IHyperlink[] detectHyperlinks(ITextViewer textViewer, IRegion region, boolean canShowMultipleHyperlinks) {
		if (editor == null || textViewer == null || region == null) {
			return null;
		}
		IDocument doc = textViewer.getDocument();
		if (doc == null) {
			return null;
		}
		IRegion wordRegion = ShayaDeclarations.wordRegionAtOffset(doc, region.getOffset());
		if (wordRegion == null) {
			return null;
		}
		String word;
		try {
			word = doc.get(wordRegion.getOffset(), wordRegion.getLength());
		} catch (BadLocationException e) {
			return null;
		}
		if (word.isEmpty() || Character.isDigit(word.charAt(0))) {
			return null;
		}
		if (ShayaKeywords.isKeyword(word, editor.currentDialect())) {
			return null;
		}
		IFile file = null;
		if (editor.getEditorInput() instanceof FileEditorInput) {
			file = ((FileEditorInput) editor.getEditorInput()).getFile();
		}
		List<ShayaDeclarations.Hit> hits = ShayaDeclarations.findDeclarations(doc, file, word, true);
		if (hits.isEmpty()) {
			return null;
		}
		final ShayaDeclarations.Hit hit = hits.get(0);
		return new IHyperlink[] { new IHyperlink() {
			@Override
			public IRegion getHyperlinkRegion() {
				return wordRegion;
			}

			@Override
			public String getTypeLabel() {
				return "ALG declaration";
			}

			@Override
			public String getHyperlinkText() {
				return "Open declaration of " + word;
			}

			@Override
			public void open() {
				ShayaDeclarations.openHit(editor, hit);
			}
		} };
	}
}
