package org.myau.shaya.ide.editor;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.Position;
import org.eclipse.jface.text.reconciler.DirtyRegion;
import org.eclipse.jface.text.reconciler.IReconcilingStrategy;
import org.eclipse.jface.text.reconciler.IReconcilingStrategyExtension;
import org.eclipse.jface.text.source.Annotation;
import org.eclipse.jface.text.source.projection.ProjectionAnnotation;
import org.eclipse.jface.text.source.projection.ProjectionAnnotationModel;
import org.eclipse.swt.widgets.Display;

/** Background reconcile: update folding regions + outline. */
public class ShayaReconcilingStrategy implements IReconcilingStrategy, IReconcilingStrategyExtension {

	private final ShayaEditor editor;
	private IDocument document;

	public ShayaReconcilingStrategy(ShayaEditor editor) {
		this.editor = editor;
	}

	@Override
	public void setDocument(IDocument document) {
		this.document = document;
	}

	@Override
	public void reconcile(DirtyRegion dirtyRegion, IRegion subRegion) {
		reconcile(subRegion);
	}

	@Override
	public void reconcile(IRegion partition) {
		if (document == null || editor == null) {
			return;
		}
		ShayaCommentStyle style = ShayaCommentStyle.forDialect(editor.currentDialect());
		final List<Position> positions = ShayaFoldingComputer.computeFoldingPositions(document, style);
		Display.getDefault().asyncExec(() -> {
			ProjectionAnnotationModel model = editor.getProjectionAnnotationModel();
			if (model != null) {
				applyFolding(model, positions);
			}
			editor.refreshOutline();
		});
	}

	private static void applyFolding(ProjectionAnnotationModel model, List<Position> positions) {
		Annotation[] removals = null;
		synchronized (model) {
			List<Annotation> old = new ArrayList<>();
			Iterator<?> it = model.getAnnotationIterator();
			while (it.hasNext()) {
				Object next = it.next();
				if (next instanceof ProjectionAnnotation) {
					old.add((Annotation) next);
				}
			}
			removals = old.toArray(new Annotation[0]);
		}
		Map<Annotation, Position> additions = new HashMap<>();
		for (Position p : positions) {
			additions.put(new ProjectionAnnotation(), p);
		}
		model.modifyAnnotations(removals, additions, null);
	}

	@Override
	public void setProgressMonitor(IProgressMonitor monitor) {
	}

	@Override
	public void initialReconcile() {
		reconcile((IRegion) null);
	}
}
