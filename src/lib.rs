use pyo3::{prelude::*, exceptions::PyRuntimeError, exceptions};
mod executioner;
mod analizer;
mod fold_check;

#[pyfunction]
#[pyo3(signature = (s, exec_path = ""))]
fn execute_string(py: Python<'_>, s: String, exec_path: &str) -> PyResult<()> {
    py.allow_threads(|| {
        let mut exec = match analizer::parse_str(s) {
            Ok(ex) => ex,
            Err(e) => return Err(PyRuntimeError::new_err(e))
        };
    
        if exec_path == "" {
            match exec.execute_all() {
                Ok(_) => Ok(()),
                Err(e) => Err(PyRuntimeError::new_err(e))
            }
        }
        else {
            match exec.execute_in_path(exec_path) {
                Ok(_) => Ok(()),
                Err(e) => Err(PyRuntimeError::new_err(e))
            }
        }
    })
}

#[pyfunction]
#[pyo3(signature = (path, exec_path = ""))]
fn execute_file(py: Python<'_>, path: &str, exec_path: &str) -> PyResult<()> {
    py.allow_threads(|| {
        let mut exec = match analizer::parse_file(path) {
            Ok(ex) => ex,
            Err(e) => return Err(PyRuntimeError::new_err(e))
        };
    
        if exec_path == "" {
            match exec.execute_all() {
                Ok(_) => Ok(()),
                Err(e) => Err(PyRuntimeError::new_err(e))
            }
        }
        else {
            match exec.execute_in_path(exec_path) {
                Ok(_) => Ok(()),
                Err(e) => Err(PyRuntimeError::new_err(e))
            }
        }
    })
}

#[pyfunction]
fn check_string(s: String) -> PyResult<()> {
    match analizer::check_code(s) {
        Ok(_) => Ok(()),
        Err(e) => Err(exceptions::PySyntaxError::new_err(e))
    }
}

/// A Python module implemented in Rust.
#[pymodule]
#[pyo3(name = "execution")]
fn execution(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(execute_string, m)?)?;
    m.add_function(wrap_pyfunction!(execute_file, m)?)?;
    m.add_function(wrap_pyfunction!(check_string, m)?)?;
    Ok(())
}