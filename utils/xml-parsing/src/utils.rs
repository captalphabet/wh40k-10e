use regex::Regex;
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader, Read};
use std::path::Path;
use thiserror::Error;
use tracing::info;

pub fn read_xml_file<T>(path: T) -> std::io::Result<String>
where
    T: AsRef<Path>,
{
    let path: &Path = path.as_ref();
    let file = File::open(path)?;
    let mut reader = BufReader::new(file);
    let mut output = String::new();
    reader.read_to_string(&mut output)?;
    Ok(output)
}

pub fn _walk_tree(data: &str) {
    // walk each <> tag irregardless if closing
    let tag_pattern = Regex::new(r"<.+>").unwrap();

    // let mut open_tags: Vec<Tag> = Vec::new();
    // let mut close_tags: Vec<Tag> = Vec::new();
    let mut num_openers = 0;
    let mut num_closers = 0;
    let mut unparsed_tags = 0;

    tag_pattern
        .find_iter(data)
        .map(|found_tag| {
            let tag_str = found_tag.as_str();

            if tag_str.starts_with("</") {
                if _handle_closing_tag(tag_str).is_some() {
                    num_closers += 1;
                } else {
                    unparsed_tags += 1;
                    info!("Unparsed Tag: {}", tag_str);
                }
            } else {
                if _handle_opening_tag(tag_str).is_some() {
                    num_openers += 1;
                } else {
                    unparsed_tags += 1;
                    info!("Unparsed Tag: {}", tag_str);
                }
            };
        })
        .for_each(drop);
    info!("Number of unparded tags: {:?}", unparsed_tags);
    info!("Number of parsed opener tags: {:?}", num_openers);
    info!("Number of parsed closer tags: {:?}", num_closers);
}

fn _handle_opening_tag(tag: &str) -> Option<Tag> {
    let pattern = Regex::new(r"<(\w+) ?(.*)>").unwrap();
    let disassembled_opt = pattern.captures(tag).map(|cap| {
        let (_, [tag_name, metadata]) = cap.extract();

        (tag_name, metadata)
    });

    // disassembled_opt

    let meta_pattern = Regex::new(r#"(\w+)\s*=\s*(?:\"(.*?)\"|'(.*?)'|(\w+))"#).unwrap();

    disassembled_opt.map(|(tagname, metadata_str)| {
        let meta_data = MetaData {
            map: meta_pattern
                .captures_iter(metadata_str)
                .map(|cap| {
                    let (_, [key, val]) = cap.extract();

                    (key, val)
                })
                .collect(),
        };

        Tag {
            name: tagname.to_string(),
            metadata: Some(meta_data),
        } // Return Option<Tag>
    })
}

fn _handle_closing_tag(tag: &str) -> Option<Tag> {
    let pattern = Regex::new(r"</(\w+).*>").unwrap();

    pattern.captures(tag).map(|cap| {
        let (_, [tag_name]) = cap.extract();

        Tag {
            name: tag_name.to_string(),
            metadata: None,
        }
    })
}

fn _parse_tag_open(data: &str) -> Vec<Tag> {
    let re = Regex::new(r"<(\w+) ?(.*)>").unwrap();

    let openers: Vec<_> = re
        .captures_iter(data)
        .map(|cap| {
            let (_, [tag_name, metadata]) = cap.extract();

            (tag_name, metadata)
        })
        .collect();

    let meta_pattern = Regex::new(r#"(\w+)\s*=\s*(?:\"(.*?)\"|'(.*?)'|(\w+))"#).unwrap();

    let mut parsed_openers = Vec::new();

    for open in openers {
        // println!("{:?}: {:?}",open.0,open.1);
        let metadata: OptMetaData = if !open.1.is_empty() {
            let meta_matches: HashMap<_, _> = meta_pattern
                .captures_iter(open.1)
                .map(|cap| {
                    let (_, [key, val]) = cap.extract();

                    (key, val)
                })
                .collect();

            Some(MetaData { map: meta_matches })
        } else {
            None
        };

        let tag = Tag {
            name: open.0.to_string(),
            metadata,
        };

        println!("{:?}", tag.name);
        if let Some(hm) = &tag.metadata {
            hm.map
                .iter()
                .for_each(|(k, v)| println!("Key: {:?}, Val: {:?}", *k, *v));
        }

        parsed_openers.push(tag);
    }

    parsed_openers
}

pub type OptMetaData<'a> = Option<MetaData<'a>>;

#[derive(Debug, Error)]
pub enum TagParseError {
    #[error("Failed to Parse tag metadata: {0}")]
    TagMetaDataKind(String),
}

#[derive(Debug)]
struct MetaData<'a> {
    map: HashMap<&'a str, &'a str>,
}

impl<'a> MetaData<'a> {
    // Meta Data String has had name already parsed out
    pub fn try_parse<T: AsRef<str>>(value: &'a T) -> Result<Self, TagParseError> {
        let input_str = value.as_ref();

        if input_str.is_empty() {
            return Err(TagParseError::TagMetaDataKind("Input is empty".to_string()));
        }

        let it1 = input_str
            .split_whitespace()
            .filter(|split| *split!="=")
            .map(|split|         split.trim_matches('='));
        let it2 = it1.clone().skip(1);


            
        let map: HashMap<&'a str, &'a str> = it1.zip(it2).map(|v| v).collect();
            

        Ok(MetaData { map })
    }
}

#[derive(Debug)]
pub struct Tag<'a> {
    name: String,
    metadata: OptMetaData<'a>,
}
