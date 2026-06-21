export interface Child {
  id:number; child_id:string; admission_file_no:string; full_name:string; father_name:string; grandfather_name:string; mother_name:string; gender:"Male"|"Female"|"Other"; date_of_birth:string; guardian_name:string; guardian_relationship:string; guardian_cnic:string; guardian_mobile:string; current_address:string; permanent_address:string; village_mohallah:string; union_council:string; tehsil:string; district:string; province:string; admission_date:string; reason_for_admission:string; status:"Active"|"Inactive"|"Discharged"|"Transferred"; created_at:string;
}
export type ChildCreatePayload=Omit<Child,"id"|"created_at">;
export type ChildUpdatePayload=Pick<Child,"full_name"|"father_name"|"grandfather_name"|"mother_name"|"guardian_name"|"guardian_relationship"|"guardian_cnic"|"guardian_mobile"|"current_address"|"permanent_address"|"village_mohallah"|"union_council"|"tehsil"|"district"|"province"|"reason_for_admission"|"status">;
export interface ChildCompleteProfile { child_basic:Record<string,unknown>;admission_documents:Record<string,unknown>;sponsorship:Record<string,unknown>;accommodation:Record<string,unknown>;medical:Record<string,unknown>;education:Record<string,unknown>;case_management:Record<string,unknown>;daily_attendance:Record<string,unknown> }
export interface ChildDocument {id:number;child_id:number;document_type:string;original_filename:string;stored_filename:string;file_path:string;is_verified:boolean;uploaded_at?:string}
export interface ImportValidationError {row:number;field?:string;message:string;code?:string}
export interface ImportPreview {total_rows:number;valid_rows:number;invalid_rows:number;duplicate_rows:number;validation_errors:ImportValidationError[];preview_data:Record<string,unknown>[]}
export interface ImportCommit {imported_count:number;skipped_count:number;errors:ImportValidationError[];created_child_ids:number[]}
