package org.myau.shaya.ide.editor;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.jface.action.IStatusLineManager;
import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.debug.ui.actions.IToggleBreakpointsTarget;
import org.eclipse.jface.text.source.IVerticalRuler;
import org.eclipse.jface.text.source.IVerticalRulerInfo;
import org.eclipse.jface.text.source.projection.ProjectionAnnotationModel;
import org.eclipse.jface.text.source.projection.ProjectionSupport;
import org.eclipse.jface.text.source.projection.ProjectionViewer;
import org.eclipse.swt.SWT;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IEditorSite;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.editors.text.TextEditor;
import org.eclipse.ui.part.FileEditorInput;
import org.eclipse.ui.texteditor.SourceViewerDecorationSupport;
import org.eclipse.ui.views.contentoutline.IContentOutlinePage;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.debug.ShayaBreakpoints;
import org.myau.shaya.ide.outline.ShayaContentOutlinePage;
import org.myau.shaya.ide.prefs.ShayaPreferenceConstants;
import org.myau.shaya.ide.run.ShayaLastLaunch;
import org.myau.shaya.ide.run.ShayaLauncher;
import org.myau.shaya.ide.run.ShayaSourceResolver;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * ALG editor: highlighting, folding, outline, brackets, check-on-save, status line.
 */
public class ShayaEditor extends TextEditor {

	private final ShayaColorManager colorManager = new ShayaColorManager();
	private ProjectionSupport projectionSupport;
	private ShayaContentOutlinePage outlinePage;
	private ShayaOccurrenceHighlighter occurrences;
	/** Debounced check-on-save job (cancelled/rescheduled on rapid saves). */
	private Job checkOnSaveJob;
	/** Compact engine/capability status with details in tooltip. */
	private ShayaEngineStatusContribution engineStatusItem;

	public ShayaEditor() {
		super();
		setSourceViewerConfiguration(new ShayaSourceViewerConfiguration(colorManager, this));
		setDocumentProvider(new ShayaDocumentProvider());
		getPreferenceStore().setDefault("matchingBrackets", true);
		getPreferenceStore().setDefault("matchingBracketsColor", "128,128,128");
		getPreferenceStore().setDefault("hyperlinksEnabled", true);
		getPreferenceStore().setDefault("hyperlinkKeyModifierNames", "Ctrl+");
		getPreferenceStore().setDefault("hyperlinkColor", "0,0,255");
	}

	@Override
	protected void configureSourceViewerDecorationSupport(SourceViewerDecorationSupport support) {
		support.setCharacterPairMatcher(new ShayaKeywordPairMatcher(this));
		support.setMatchingCharacterPainterPreferenceKeys("matchingBrackets", "matchingBracketsColor");
		super.configureSourceViewerDecorationSupport(support);
	}

	@Override
	protected ISourceViewer createSourceViewer(Composite parent, IVerticalRuler ruler, int styles) {
		fAnnotationAccess = getAnnotationAccess();
		fOverviewRuler = createOverviewRuler(getSharedColors());
		ISourceViewer viewer = new ProjectionViewer(parent, ruler, getOverviewRuler(),
				isOverviewRulerVisible(), styles);
		getSourceViewerDecorationSupport(viewer);
		return viewer;
	}

	@Override
	public void createPartControl(Composite parent) {
		super.createPartControl(parent);
		ProjectionViewer viewer = (ProjectionViewer) getSourceViewer();
		projectionSupport = new ProjectionSupport(viewer, getAnnotationAccess(), getSharedColors());
		projectionSupport.install();
		viewer.doOperation(ProjectionViewer.TOGGLE);
		IVerticalRuler ruler = getVerticalRuler();
		if (ruler != null && ruler.getControl() != null) {
			String eng = ShayaToolchain.engineIdForName(
					getEditorInput() != null ? getEditorInput().getName() : null);
			if (ShayaToolchain.supportsStepDebugUi(eng) && ruler instanceof IVerticalRulerInfo) {
				// Double-click gutter → toggle line breakpoint (Java-like)
				ShayaBreakpoints.installRulerToggle(this, ruler.getControl(), (IVerticalRulerInfo) ruler);
			} else {
				// Other dialects: double-click gutter → Run
				ruler.getControl().addListener(SWT.MouseDoubleClick, event -> runFromEditor());
			}
		}
		updateEngineStatus();
		if (occurrences == null) {
			occurrences = new ShayaOccurrenceHighlighter(this);
			occurrences.install();
		}
	}

	private void ensureEngineStatusItem() {
		if (engineStatusItem != null) {
			return;
		}
		try {
			IStatusLineManager slm = getEditorSite().getActionBars().getStatusLineManager();
			if (slm == null) {
				return;
			}
			engineStatusItem = new ShayaEngineStatusContribution();
			slm.add(engineStatusItem);
			getEditorSite().getActionBars().updateActionBars();
		} catch (Exception ignored) {
		}
	}

	/** Ruler double-click / toolbar: save dirty buffer and Run. */
	private void runFromEditor() {
		try {
			if (isDirty()) {
				doSave(null);
			}
			ShayaSourceResolver.ResolvedSource src = ShayaSourceResolver.resolveFromEditor(this);
			if (src == null) {
				return;
			}
			ShayaLastLaunch.remember(ShayaLastLaunch.Mode.RUN, src);
			ShayaLauncher.run(src.file, src.workspaceFile);
		} catch (Exception ignored) {
		}
	}

	@Override
	public void init(IEditorSite site, IEditorInput input) throws PartInitException {
		super.init(site, input);
		updateEngineStatus();
	}

	@Override
	protected void doSetInput(IEditorInput input) throws CoreException {
		super.doSetInput(input);
		updateEngineStatus();
	}

	@Override
	public void setFocus() {
		super.setFocus();
		updateEngineStatus();
	}

	/** Dialect for the currently open file — drives keyword highlighting / templates. */
	public ShayaKeywords.Dialect currentDialect() {
		String name = getEditorInput() != null ? getEditorInput().getName() : null;
		return ShayaKeywords.dialectOfFileName(name);
	}

	/** Status line: which engine this extension maps to (extension -> engine law). */
	private void updateEngineStatus() {
		try {
			if (getEditorSite() == null || getEditorSite().getActionBars() == null) {
				return;
			}
			ensureEngineStatusItem();
			IStatusLineManager slm = getEditorSite().getActionBars().getStatusLineManager();
			if (slm == null) {
				return;
			}
			String name = getEditorInput() != null ? getEditorInput().getName() : "";
			String engineId = ShayaToolchain.engineIdForName(name);
			String engine = engineId != null ? ShayaToolchain.engineDisplayName(engineId) : "unknown extension";
			ShayaCommentStyle cs = ShayaCommentStyle.forDialect(currentDialect());
			String comment = cs == ShayaCommentStyle.LINE_PIPE ? "|"
					: (cs == ShayaCommentStyle.BLOCK_PAREN ? "(* *)" : "//");
			boolean canCheck = engineId != null && ShayaToolchain.supportsCheck(engineId);
			boolean canTr = engineId != null && ShayaToolchain.supportsTranspile(engineId);
			boolean canStep = engineId != null && ShayaToolchain.supportsStepDebugUi(engineId);
			String check = canCheck ? "C✓" : "C—";
			String tr = canTr ? "T✓" : "T—";
			String step = canStep ? "S✓" : "S—";
			String msg = "ALG · " + engine;
			IPreferenceStore prefs = Activator.getDefault() != null
					? Activator.getDefault().getPreferenceStore() : null;
			boolean saveNa = prefs != null && prefs.getBoolean(ShayaPreferenceConstants.CHECK_ON_SAVE) && !canCheck;
			if (saveNa) {
				msg += " · save N/A";
			}
			String tip = "Engine: " + engine
					+ "\nCheck: " + (canCheck ? "yes" : "no")
					+ " · Transpile: " + (canTr ? "yes" : "no")
					+ " · Step Debug: " + (canStep ? "yes" : "no")
					+ "\nComments: " + comment
					+ " · Plugin: v" + shortVersion()
					+ "\nFile: " + name
					+ (saveNa ? "\nCheck on save: N/A for this engine" : "");
			slm.setMessage(msg);
			if (engineStatusItem != null) {
				engineStatusItem.setText(check + " " + tr + " " + step);
				engineStatusItem.setToolTipText(tip);
			}
		} catch (Exception ignored) {
		}
	}

	private static String shortVersion() {
		try {
			if (Activator.getDefault() != null && Activator.getDefault().getBundle() != null) {
				return Activator.getDefault().getBundle().getVersion().toString();
			}
		} catch (Exception ignored) {
		}
		return "?";
	}

	public ISourceViewer getSourceViewerPublic() {
		return getSourceViewer();
	}

	public ProjectionAnnotationModel getProjectionAnnotationModel() {
		ISourceViewer viewer = getSourceViewer();
		if (viewer instanceof ProjectionViewer) {
			return ((ProjectionViewer) viewer).getProjectionAnnotationModel();
		}
		return null;
	}

	public IDocument getEditorDocument() {
		if (getDocumentProvider() == null || getEditorInput() == null) {
			return null;
		}
		return getDocumentProvider().getDocument(getEditorInput());
	}

	public void refreshOutline() {
		if (outlinePage != null) {
			outlinePage.refresh();
		}
	}

	@Override
	@SuppressWarnings("unchecked")
	public <T> T getAdapter(Class<T> adapter) {
		if (IContentOutlinePage.class.equals(adapter)) {
			if (outlinePage == null) {
				outlinePage = new ShayaContentOutlinePage(this);
			}
			return (T) outlinePage;
		}
		if (IToggleBreakpointsTarget.class.equals(adapter)) {
			String eng = ShayaToolchain.engineIdForName(
					getEditorInput() != null ? getEditorInput().getName() : null);
			if (ShayaToolchain.supportsStepDebugUi(eng)) {
				return (T) new org.myau.shaya.ide.debug.ShayaToggleBreakpointsTarget();
			}
		}
		if (projectionSupport != null) {
			T adapted = projectionSupport.getAdapter(getSourceViewer(), adapter);
			if (adapted != null) {
				return adapted;
			}
		}
		return super.getAdapter(adapter);
	}

	@Override
	protected void editorSaved() {
		super.editorSaved();
		IPreferenceStore prefs = Activator.getDefault().getPreferenceStore();
		if (prefs == null || !prefs.getBoolean(ShayaPreferenceConstants.CHECK_ON_SAVE)) {
			return;
		}
		if (!(getEditorInput() instanceof FileEditorInput)) {
			return;
		}
		if (isDirty()) {
			return;
		}
		final IFile file = ((FileEditorInput) getEditorInput()).getFile();
		if (file == null || !file.exists()) {
			return;
		}
		String engine = ShayaToolchain.engineIdForName(file.getName());
		if (engine == null || !ShayaToolchain.supportsCheck(engine)) {
			return;
		}
		if (checkOnSaveJob != null) {
			checkOnSaveJob.cancel();
		}
		checkOnSaveJob = new Job("ALG check on save: " + file.getName()) {
			@Override
			protected IStatus run(IProgressMonitor monitor) {
				if (monitor.isCanceled()) {
					return Status.CANCEL_STATUS;
				}
				int rc = ShayaLauncher.checkSync(file, monitor);
				return rc == 0 ? Status.OK_STATUS
						: new Status(IStatus.WARNING, Activator.PLUGIN_ID, "check on save exit=" + rc);
			}
		};
		checkOnSaveJob.setSystem(true);
		checkOnSaveJob.schedule(700);
	}

	@Override
	public void dispose() {
		if (occurrences != null) {
			occurrences.uninstall();
			occurrences = null;
		}
		outlinePage = null;
		colorManager.dispose();
		super.dispose();
	}
}
