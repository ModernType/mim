mod executioner;
mod analizer;


fn main() {
    
}


#[test]
fn test_executioner() {
    use executioner::{Executioner, RunCom};
    let mut exec = Executioner::new();
    let run_com = RunCom::new("C:\\shader.exe".to_string());
    exec.push(Box::new(run_com));
    println!("{:?}", exec);
}


#[test]
fn test_prog_open() {
    use std::process::Command;
    Command::new("C:\\shader.exe").status().unwrap();
}

#[test]
fn unzip_test() {
    extern crate zip;
    use std::fs;
    let file = fs::File::open("arc.zip").unwrap();
    let mut archive = zip::ZipArchive::new(file).unwrap();
    archive.extract("arc\\folder\\anything").unwrap();
}