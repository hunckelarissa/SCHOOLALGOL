package org.myau.shaya.ide.editor;

import org.eclipse.jface.text.IAutoEditStrategy;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.ITextHover;
import org.eclipse.jface.text.contentassist.ContentAssistant;
import org.eclipse.jface.text.contentassist.IContentAssistant;
import org.eclipse.jface.text.hyperlink.IHyperlinkDetector;
import org.eclipse.jface.text.presentation.IPresentationReconciler;
import org.eclipse.jface.text.presentation.PresentationReconciler;
import org.eclipse.jface.text.reconciler.IReconciler;
import org.eclipse.jface.text.reconciler.MonoReconciler;
import org.eclipse.jface.text.rules.DefaultDamagerRepairer;
import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.jface.text.source.SourceViewerConfiguration;

/** ALG source viewer: highlighting, content assist, reconciler (folding/outline). */
public class ShayaSourceViewerConfiguration extends SourceViewerConfiguration {

	private final ShayaColorManager colorManager;
	private final ShayaEditor editor;
	private ShayaCodeScanner scanner;
	private ShayaKeywords.Dialect scannerDialect;

	public ShayaSourceViewerConfiguration(ShayaColorManager colorManager, ShayaEditor editor) {
		this.colorManager = colorManager;
		this.editor = editor;
	}

	private ShayaCodeScanner getCodeScanner() {
		ShayaKeywords.Dialect dialect = editor.currentDialect();
		if (scanner == null || scannerDialect != dialect) {
			scanner = new ShayaCodeScanner(colorManager, dialect);
			scannerDialect = dialect;
		}
		return scanner;
	}

	@Override
	public IPresentationReconciler getPresentationReconciler(ISourceViewer sourceViewer) {
		PresentationReconciler reconciler = new PresentationReconciler();
		DefaultDamagerRepairer dr = new DefaultDamagerRepairer(getCodeScanner());
		reconciler.setDamager(dr, IDocument.DEFAULT_CONTENT_TYPE);
		reconciler.setRepairer(dr, IDocument.DEFAULT_CONTENT_TYPE);
		return reconciler;
	}

	@Override
	public IContentAssistant getContentAssistant(ISourceViewer sourceViewer) {
		ContentAssistant assistant = new ContentAssistant();
		assistant.setContentAssistProcessor(new ShayaCompletionProcessor(editor),
				IDocument.DEFAULT_CONTENT_TYPE);
		assistant.enableAutoActivation(true);
		assistant.setAutoActivationDelay(300);
		assistant.setProposalPopupOrientation(IContentAssistant.PROPOSAL_OVERLAY);
		assistant.setContextInformationPopupOrientation(IContentAssistant.CONTEXT_INFO_ABOVE);
		return assistant;
	}

	@Override
	public ITextHover getTextHover(ISourceViewer sourceViewer, String contentType) {
		return new ShayaTextHover(editor);
	}

	@Override
	public IHyperlinkDetector[] getHyperlinkDetectors(ISourceViewer sourceViewer) {
		return new IHyperlinkDetector[] { new ShayaHyperlinkDetector(editor) };
	}

	@Override
	public IAutoEditStrategy[] getAutoEditStrategies(ISourceViewer sourceViewer, String contentType) {
		return new IAutoEditStrategy[] {
				new ShayaAutoIndentStrategy(),
				new ShayaSmartTypingStrategy()
		};
	}

	@Override
	public String[] getIndentPrefixes(ISourceViewer sourceViewer, String contentType) {
		String unit = ShayaIndent.unit();
		return new String[] { unit, "\t", "" };
	}

	@Override
	public int getTabWidth(ISourceViewer sourceViewer) {
		return ShayaIndent.width();
	}

	@Override
	public IReconciler getReconciler(ISourceViewer sourceViewer) {
		ShayaReconcilingStrategy strategy = new ShayaReconcilingStrategy(editor);
		MonoReconciler reconciler = new MonoReconciler(strategy, false);
		reconciler.setDelay(400);
		return reconciler;
	}

	@Override
	public String[] getConfiguredContentTypes(ISourceViewer sourceViewer) {
		return new String[] { IDocument.DEFAULT_CONTENT_TYPE };
	}

	@Override
	public String[] getDefaultPrefixes(ISourceViewer sourceViewer, String contentType) {
		ShayaCommentStyle style = ShayaCommentStyle.forDialect(editor.currentDialect());
		if (style == ShayaCommentStyle.LINE_PIPE) {
			return new String[] { "| ", "|" };
		}
		if (style == ShayaCommentStyle.BLOCK_PAREN) {
			// Vetka_B: Toggle Comment uses (* *); prefix API has no block closer — leave empty.
			return new String[] { "" };
		}
		return new String[] { "// ", "//" };
	}
}
