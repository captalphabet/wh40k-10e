use crate::utils::{Tag,OptMetaData};

// Manually parse tags, Regex is slow
//
//

pub fn detect_tag(input: &str) {
    //! Detects and parses out all < > delimited tags
    let data_iter = input.char_indices();

    let mut in_tag: bool = false;
    let mut tag_collection = vec![];
    let mut buffer = String::new();
    for (i, numeral) in data_iter {
        match numeral {
            '<' => {
                in_tag = true;
                continue;
            }
            '>' => {
                in_tag = false;
                tag_collection.push(buffer.clone());
                continue;
            }
            _ => (),
        }

        if in_tag {
            buffer.push(numeral);
        } else if !buffer.is_empty() {
            buffer.clear();
        }
    }
}

#[derive(Debug)]
enum TagType {
    Open,
    Close,
    SelfClose,
}

impl TagType {
    fn check_tag_type(tag_str: &str) -> TagType {
        if tag_str.starts_with('/') {
            TagType::Close
        } else if tag_str.ends_with("/") {
            TagType::SelfClose
        } else {
            TagType::Open
        }
    }
}

impl<'a,T> From<&'a T> for Tag<'a>
where T: AsRef<str> {
    fn from(value: &'a T) -> Self {
        let tag_str = value.as_ref();
        if let Some((name,meta_data)) = tag_str.split_once(' ') {

        }


        
    }

}


// fn parse_tag_data(tag_str: &str, typing: TagType) -> (Tag, TagType) {
//     match typing {
//         Open => {
//             // Needs to parse name out and metadata
//             let mut tag_content_iter = tag_str.split_whitespace();
//             let tag_name = tag_content_iter.next().unwrap_or("NoName");
//             let meta_data_vec = tag_content_iter.collect::<Vec<_>>();
//         }
//         Close => {}
//         SelfClose => {}
//     }
// }
