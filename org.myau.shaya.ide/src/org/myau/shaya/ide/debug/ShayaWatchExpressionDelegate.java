package org.myau.shaya.ide.debug;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.debug.core.DebugException;
import org.eclipse.debug.core.model.IDebugElement;
import org.eclipse.debug.core.model.IDebugTarget;
import org.eclipse.debug.core.model.IValue;
import org.eclipse.debug.core.model.IWatchExpressionDelegate;
import org.eclipse.debug.core.model.IWatchExpressionListener;
import org.eclipse.debug.core.model.IWatchExpressionResult;
import org.myau.shaya.ide.Activator;
import org.myau.shaya.ide.debug.model.ShayaDebugTarget;
import org.myau.shaya.ide.debug.model.ShayaValue;

/**
 * Expressions view: {@code eval} over SHAYDBG while suspended.
 */
public class ShayaWatchExpressionDelegate implements IWatchExpressionDelegate {

	@Override
	public void evaluateExpression(String expression, IDebugElement context,
			IWatchExpressionListener listener) {
		Job job = new Job("ALG evaluate: " + expression) {
			@Override
			protected IStatus run(IProgressMonitor monitor) {
				try {
					ShayaDebugTarget target = findTarget(context);
					if (target == null || !target.isSuspended()) {
						listener.watchEvaluationFinished(errorResult(expression, "not suspended"));
						return Status.OK_STATUS;
					}
					String value = target.evaluate(expression);
					IValue ivalue = new ShayaValue(target, value);
					listener.watchEvaluationFinished(okResult(expression, ivalue));
				} catch (Exception e) {
					String msg = e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
					listener.watchEvaluationFinished(errorResult(expression, msg));
				}
				return Status.OK_STATUS;
			}
		};
		job.setSystem(true);
		job.schedule();
	}

	private static ShayaDebugTarget findTarget(IDebugElement context) {
		if (context == null) {
			return null;
		}
		IDebugTarget t = context.getDebugTarget();
		if (t instanceof ShayaDebugTarget) {
			return (ShayaDebugTarget) t;
		}
		return null;
	}

	private static IWatchExpressionResult okResult(String expression, IValue value) {
		return new IWatchExpressionResult() {
			@Override
			public IValue getValue() {
				return value;
			}

			@Override
			public boolean hasErrors() {
				return false;
			}

			@Override
			public String[] getErrorMessages() {
				return new String[0];
			}

			@Override
			public String getExpressionText() {
				return expression;
			}

			@Override
			public DebugException getException() {
				return null;
			}
		};
	}

	private static IWatchExpressionResult errorResult(String expression, String message) {
		return new IWatchExpressionResult() {
			@Override
			public IValue getValue() {
				return null;
			}

			@Override
			public boolean hasErrors() {
				return true;
			}

			@Override
			public String[] getErrorMessages() {
				return new String[] { message };
			}

			@Override
			public String getExpressionText() {
				return expression;
			}

			@Override
			public DebugException getException() {
				return new DebugException(new Status(IStatus.ERROR, Activator.PLUGIN_ID, message));
			}
		};
	}
}
