use std::{fmt::Debug, process::Command as OpenProgram, fs, path::{Path, PathBuf}, io::ErrorKind, io::Write};
extern crate zip;
extern crate open;

pub trait Command: Debug {
    fn execute(&self) -> Result<(), String>;
    fn add_to_relative(&mut self, s: &str);
}

#[derive(Debug)]
pub struct RunCom {
    path: String
}

impl Command for RunCom {
    fn execute(&self) -> Result<(), String> {
        if self.path.ends_with(".exe") || self.path.ends_with(".msi") {
            match OpenProgram::new(&self.path).status() {
                Ok(_) => Ok(()),
                Err(e) => Err(e.to_string())
            }
        }
        else {
            match open::that(&self.path) {
                Ok(_) => Ok(()),
                Err(e) => Err(e.to_string())
            }
        }
    }

    fn add_to_relative(&mut self, s: &str) {
        if !self.path.contains(':') { self.path = format!("{}\\{}", s, self.path); }
    }
}

impl RunCom {
    pub fn new(path: String) -> Self {
        RunCom { path }
    }
}


#[derive(Debug)]
pub struct CopyCom {
    from_path: String,
    to_path: String
}

impl Command for CopyCom {
    fn execute(&self) -> Result<(), String> {
        let from = Path::new(&self.from_path);
        let mut to = Path::new(&self.to_path);
        let mut buf: PathBuf;
        if to.is_dir() {
            buf = to.to_path_buf();
            buf.push(from.file_name().unwrap());
            to = buf.as_path();
        }
        match fs::copy(from, to) {
            Ok(_) => Ok(()),
            Err(e) => match e.kind() {
                ErrorKind::NotFound => Err(format!("File {} not found", self.from_path)),
                _ => Err(format!("Error copying {} to {}: {}", self.from_path, self.to_path, e.to_string()))
            }
        }
    }

    fn add_to_relative(&mut self, s: &str) {
        if !self.from_path.contains(':') {self.from_path = format!("{}\\{}", s, self.from_path);}
        if !self.to_path.contains(':') {self.to_path = format!("{}\\{}", s, self.to_path);}
    }
}

impl CopyCom {
    pub fn new(from_path: String, to_path: String) -> Self {
        CopyCom {from_path, to_path}
    }
}


#[derive(Debug)]
pub struct ShellCom {
    shell_com: String
}

impl Command for ShellCom {
    fn execute(&self) -> Result<(), String> {
        match OpenProgram::new("cmd").args(["/C", self.shell_com.as_str()]).spawn() {
            Ok(_) => Ok(()),
            Err(e) => Err(format!("Failed to execute command {} due to {}", self.shell_com, e.to_string()))
        }
    }

    fn add_to_relative(&mut self, s: &str) {
        if !self.shell_com.contains(':') {self.shell_com = format!("{}\\{}", s, self.shell_com);}
    }
}

impl ShellCom {
    pub fn new(shell_com: String) -> Self {
        ShellCom {shell_com}
    }
}

#[derive(Debug)]
pub struct UnzipCom {
    file_path: String,
    to_path: String
}

impl Command for UnzipCom {
    fn execute(&self) -> Result<(), String> {
        let file = match fs::File::open(&self.file_path) {
            Ok(f) => f,
            Err(e) => return Err(format!("Error opening file: {}", e.to_string()))
        };
        let mut arc = match zip::ZipArchive::new(file) {
            Ok(a) => a,
            Err(e) => return Err(format!("Is file a zip format? {}", e.to_string()))
        };
        match arc.extract(&self.to_path) {
            Ok(_) => {},
            Err(e) => return Err(format!("Error extracting files: {}", e.to_string()))
        }

        Ok(())
    }

    fn add_to_relative(&mut self, s: &str) {
        if !self.file_path.contains(':') {self.file_path = format!("{}\\{}", s, self.file_path);}
        if !self.to_path.contains(':') {self.to_path = format!("{}\\{}", s, self.to_path);}
    }
}

impl UnzipCom {
    pub fn new(file_path: String, to_path: String) -> UnzipCom {
        UnzipCom { file_path, to_path }
    }
}


#[derive(Debug)]
pub struct RemoveCom {
    path: String
}

impl Command for RemoveCom {
    fn execute(&self) -> Result<(), String> {
        match fs::remove_file(&self.path) {
            Ok(_) => Ok(()),
            Err(_) => {
                match fs::remove_dir_all(&self.path) {
                    Ok(_) => Ok(()),
                    Err(_) => Err(format!("Error removing file {}", &self.path))
                }
            }
        }
    }

    fn add_to_relative(&mut self, s: &str) {
        if !self.path.contains(':') {self.path = format!("{}\\{}", s, self.path);}
    }
}

impl RemoveCom {
    pub fn new(path: String) -> RemoveCom {
        RemoveCom { path }
    }
}


#[derive(Debug)]
pub struct RenameCom {
    path: String,
    new_name: String
}

impl Command for RenameCom {
    fn execute(&self) -> Result<(), String> {
        let mut spl: Vec<&str> = (&self.path).split('\\').collect();
        spl.pop();
        let mut new_path = spl.join("\\");
        new_path.push_str(self.new_name.as_str());

        match fs::rename(&self.path, new_path) {
            Ok(_) => Ok(()),
            Err(e) => Err(format!("Error renaming: {}", e.to_string()))
        }
    }

    fn add_to_relative(&mut self, s: &str) {
        if !self.path.contains(':') {self.path = format!("{}\\{}", s, self.path);}
    }
}

impl RenameCom {
    pub fn new(path: String, new_name: String) -> RenameCom {
        RenameCom{path, new_name}
    }
}


#[derive(Debug)]
pub struct InfoCom {
    pub message: String
}

impl Command for InfoCom {
    fn execute(&self) -> Result<(), String> {
        println!("{}", &self.message);
        Ok(())
    }

    #[allow(unused_variables)]
    fn add_to_relative(&mut self, s: &str) {}
}

impl InfoCom {
    pub fn new(message: String) -> InfoCom {
        InfoCom { message }
    }
}


#[derive(Debug)]
pub struct Executioner {
    pub commands: Vec<Box<dyn Command>>,
}

impl Executioner {
    pub fn new() -> Self {
        Executioner { commands: Vec::new() }
    }

    fn log_res(s: &str) {
        let mut file = fs::OpenOptions::new().create(true).write(true).open("error.log").unwrap();
        file.write_all(s.as_bytes()).unwrap();
    }

    pub fn push(&mut self, command: Box<dyn Command>) {
        self.commands.push(command);
    }

    pub fn execute_all(&self) -> Result<(), String> {
        for c in self.commands.iter() {
            match c.execute() {
                Ok(_) => {},
                Err(e) => {
                    // Executioner::log_res(&e);
                    return Err(format!("Error in command {:?}: {}", c, e))
                }
            }
        }

        Ok(())
    }

    pub fn execute_in_path(&mut self, path: &str) -> Result<(), String> {
        for c in self.commands.iter_mut() {
            c.add_to_relative(path);
            match c.execute() {
                Ok(_) => {},
                Err(e) => {
                    // Executioner::log_res(&e);
                    return Err(format!("Error in command {:?}: {}", c, e))
                }
            }
        }

        Ok(())
    }
}
