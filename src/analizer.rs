use std::{collections::VecDeque, cell::RefCell, fs::{File}, io::Read};

use crate::executioner::*;

struct Rule<'a> {
    pub name: &'a str,
    pub args: usize
}

#[allow(non_upper_case_globals)]
const rules: [Rule; 8] = [
    Rule{name: "run", args: 1},
    Rule{name: "copy", args: 2},
    Rule{name: "shell", args: 1},
    Rule{name: "unzip_to", args: 2},
    Rule{name: "unzip", args: 1},
    Rule{name: "remove", args: 1},
    Rule{name: "rename", args: 2},
    Rule{name: "info", args: 1}
];


pub fn parse_str(com_str: String) -> Result<Executioner, String> {
    let mut cur = String::new();
    let mut cur_line = 1u32;
    let mut exec = Executioner::new();
    let mut args: VecDeque<String> = VecDeque::new();
    let mut cur_rule: Option<&Rule> = None;
    let mut opened = false;
    
    let mut com_str = RefCell::new(com_str);
    let com_str = com_str.get_mut();

    if !com_str.ends_with('\n') { com_str.push('\n'); } // So the code to add command will trigger on the last one

    for c in com_str.chars() {
        match c {
            ' ' => { 
                if opened {
                    cur.push(c);
                    continue;
                }
                match cur_rule {
                None => {for r in rules.iter() {
                    if r.name == cur {cur_rule = Some(r)}
                }
                if let None = cur_rule {cur.push(c); continue;} // {return Err(format!("Wrong command \"{}\" in line {}. If you write a path which has spaces, consider using \" around it", cur, cur_line));}
                cur = "".to_string(); }

                Some(r) => {
                    if r.name == "shell" || r.name == "info" {
                        cur.push(c);
                    }
                    else {
                    args.push_back(cur);
                    cur = "".to_string();
                    }
                }
            }
        },
            '\n' => {
                if opened {
                    return Err(format!("Captions (\") not closed at line {}", cur_line));
                }

                let rule = match cur_rule {
                    None => {
                        let run_com = RunCom::new(cur);
                        exec.push(Box::new(run_com));
                        cur = "".to_string();
                        cur_line += 1;
                        continue;
                    },
                    Some(r) => r
                };

                args.push_back(cur);
                cur = "".to_string();

                if args.len() < rule.args { return Err(format!("Not enough arguments for command \"{}\" in line {}. Expected {} got {}", rule.name, cur_line, rule.args, args.len())); }
                else if args.len() > rule.args { return Err(format!("Too many arguments for command \"{}\" in line {}. Expected {} got {}. If there is path which has spaces consider using \" around path", rule.name, cur_line, rule.args, args.len())); }
                else {
                    match rule.name {
                        "run" => {
                            let path = args.pop_front().unwrap();
                            let run_com = RunCom::new(path);
                            exec.push(Box::new(run_com));
                        },
                        "copy" => {
                            let path_from = args.pop_front().unwrap();
                            let path_to = args.pop_front().unwrap();
                            let run_com = CopyCom::new(path_from, path_to);
                            exec.push(Box::new(run_com));
                        },
                        "shell" => {
                            let com = args.pop_front().unwrap();
                            let run_com = ShellCom::new(com);
                            exec.push(Box::new(run_com));
                        },
                        "unzip" => {
                            let file_path = args.pop_front().unwrap();
                            let to_path = file_path.clone().trim_end_matches(".zip").to_string();
                            let run_com = UnzipCom::new(file_path, to_path);
                            exec.push(Box::new(run_com));   
                        },
                        "unzip_to" => {
                            let file_path = args.pop_front().unwrap();
                            let to_path = args.pop_front().unwrap();
                            let run_com = UnzipCom::new(file_path, to_path);
                            exec.push(Box::new(run_com));
                        }
                        "remove" => {
                            let path = args.pop_front().unwrap();
                            let run_com = RemoveCom::new(path);
                            exec.push(Box::new(run_com));
                        },
                        "rename" => {
                            let path = args.pop_front().unwrap();
                            let new_name = args.pop_front().unwrap();
                            let run_com = RenameCom::new(path, new_name);
                            exec.push(Box::new(run_com));
                        },
                        "info" => {
                            let message = args.pop_front().unwrap();
                            let run_com = InfoCom::new(message);
                            exec.push(Box::new(run_com));
                        }
                        _ => { return Err("Command not implemented".to_string()); }
                    }
                }

                args.clear();
                cur_rule = None;
                cur_line += 1;
            },
            // '#' => { ignore = true; }
            '\r' => continue,
            '"' => { opened = !opened; }
            _ => { 
                cur.push(c); 
            }
        }
    }

    Ok(exec)
}


pub fn parse_file(path: &str) -> Result<Executioner, String> {
    let mut f = match File::open(path) {
        Ok(f) => f,
        Err(e) => return Err(format!("Error opening file {}: {}", path, e.to_string()))
    };
    let mut com_str = String::new();
    match f.read_to_string(&mut com_str) {
        Ok(_) => {},
        Err(e) => return Err(format!("Error reading file {}: {}", path, e.to_string()))
    };
    parse_str(com_str)
}


pub fn check_code(com_str: String) -> Result<(), String> {
    let mut cur = String::new();
    let mut cur_line = 1u32;
    let mut args: VecDeque<String> = VecDeque::new();
    let mut cur_rule: Option<&Rule> = None;
    let mut opened = false;
    
    let mut com_str = RefCell::new(com_str);
    let com_str = com_str.get_mut();

    if !com_str.ends_with('\n') { com_str.push('\n'); } // So the code to add command will triger on the last one

    for c in com_str.chars() {
        match c {
            ' ' => { 
                if opened {
                    cur.push(c);
                    continue;
                }
                match cur_rule {
                None => {for r in rules.iter() {
                    if r.name == cur {cur_rule = Some(r)}
                }
                if let None = cur_rule {cur.push(c); continue; } // {return Err(format!("Wrong command \"{}\" in line {}", cur, cur_line));}
                cur = "".to_string(); }

                Some(r) => {
                    if r.name == "shell" || r.name == "info" {
                        cur.push(c);
                    }
                    else {
                    args.push_back(cur);
                    cur = "".to_string();
                    }
                }
            }
        },
            '\n' => {
                if opened {
                    return Err(format!("Captions (\") are not closed at line {}", cur_line));
                }

                let rule = match cur_rule {
                    None => {
                        cur = "".to_string();
                        cur_line += 1;
                        continue;
                    },
                    Some(r) => r
                };

                args.push_back(cur);
                cur = "".to_string();

                if args.len() < rule.args { return Err(format!("Not enough arguments for command \"{}\" in line {}. Expected {} got {}", rule.name, cur_line, rule.args, args.len())); }
                else if args.len() > rule.args { return Err(format!("Too many arguments for command \"{}\" in line {}. Expected {} got {}. If there is path which has spaces consider using \" around it", rule.name, cur_line, rule.args, args.len())); }
                else {
                    match rule.name {
                        "run" => {},
                        "copy" => {},
                        "shell" => {},
                        "unzip" => {},
                        "unzip_to" => {}
                        "remove" => {},
                        "rename" => {},
                        "info" => {}
                        _ => { return Err("Command not implemented".to_string()); }
                    }
                }

                args.clear();
                cur_rule = None;
                cur_line += 1;
            },
            // '#' => { ignore = true; }
            '\r' => continue,
            '"' => { opened = !opened; }
            _ => { 
                cur.push(c); 
            }
        }
    }

    Ok(())
}